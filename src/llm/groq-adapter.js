// src/llm/groq-adapter.js
// Groq API adapter with:
//   - dual API key rotation on daily-limit (TPD) exhaustion
//   - model selection: fast (8b) for classification, powerful (70b) for scoring/codegen

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions';

export const GROQ_MODEL_FAST    = 'llama-3.1-8b-instant';     // classification — ~3k tokens/call
export const GROQ_MODEL_POWERFUL = 'llama-3.3-70b-versatile'; // scoring, codegen — ~8k tokens/call

// Track which key is currently active (index into KEYS array)
let activeKeyIndex = 0;

function getKeys() {
  const keys = [
    process.env.GROQ_API_KEY,
    process.env.GROQ_API_KEY_2,
  ].filter(Boolean);
  if (!keys.length) throw new Error('No GROQ_API_KEY defined in environment');
  return keys;
}

/**
 * Call Groq API with system + user prompt.
 * @param {string} systemPrompt
 * @param {string} userPrompt
 * @param {number} maxTokens
 * @param {string} model  — override default model (use GROQ_MODEL_FAST or GROQ_MODEL_POWERFUL)
 * @returns {string} raw text response
 */
export async function callGroq(systemPrompt, userPrompt, maxTokens = 4096, model = GROQ_MODEL_POWERFUL) {
  const messages = [];
  if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
  messages.push({ role: 'user', content: userPrompt });

  const MAX_RETRIES = 6;
  let attempt = 0;

  while (attempt <= MAX_RETRIES) {
    const keys = getKeys();
    const key  = keys[activeKeyIndex % keys.length];

    const res = await fetch(GROQ_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${key}`,
      },
      body: JSON.stringify({ model, max_tokens: maxTokens, messages }),
    });

    if (res.ok) {
      const data = await res.json();
      return data.choices[0].message.content.trim();
    }

    const body = await res.text();

    if (res.status === 429) {
      // Check if this is a daily-limit (TPD) error vs rate-limit (TPM) error
      const isDailyLimit = body.includes('tokens per day') || body.includes('quota') || body.includes('daily');

      if (isDailyLimit && keys.length > 1) {
        // Switch to next key permanently for this session
        const nextIndex = (activeKeyIndex + 1) % keys.length;
        if (nextIndex !== activeKeyIndex) {
          console.log(`[groq] Daily limit on key #${activeKeyIndex + 1} — switching to key #${nextIndex + 1}`);
          activeKeyIndex = nextIndex;
          attempt++;
          continue;
        }
        // Both keys exhausted
        throw new Error(`Groq daily limit exhausted on all ${keys.length} API keys`);
      }

      if (attempt < MAX_RETRIES) {
        // TPM rate limit — parse wait time from error message ("try again in X.XXs")
        const match = body.match(/try again in (\d+(?:\.\d+)?)s/i);
        const waitMs = match ? Math.ceil(parseFloat(match[1]) * 1000) + 500 : (attempt + 1) * 8000;
        console.log(`[groq] Rate limited (key #${activeKeyIndex + 1}) — waiting ${(waitMs/1000).toFixed(1)}s (attempt ${attempt+1}/${MAX_RETRIES})`);
        await new Promise(r => setTimeout(r, waitMs));
        attempt++;
        continue;
      }
    }

    throw new Error(`Groq API error ${res.status}: ${body}`);
  }

  throw new Error('Groq: max retries exceeded');
}
