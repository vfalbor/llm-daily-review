// src/llm/groq-adapter.js
// Groq API adapter — free tier, llama-3.3-70b-versatile.
// Get your free key at https://console.groq.com

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'llama-3.3-70b-versatile';

/**
 * Call Groq API with system + user prompt.
 * @param {string} systemPrompt
 * @param {string} userPrompt
 * @param {number} maxTokens
 * @returns {string} raw text response
 */
export async function callGroq(systemPrompt, userPrompt, maxTokens = 4096) {
  const messages = [];
  if (systemPrompt) messages.push({ role: 'system', content: systemPrompt });
  messages.push({ role: 'user', content: userPrompt });

  const MAX_RETRIES = 4;
  let attempt = 0;

  while (attempt <= MAX_RETRIES) {
    const res = await fetch(GROQ_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
      },
      body: JSON.stringify({ model: MODEL, max_tokens: maxTokens, messages }),
    });

    if (res.ok) {
      const data = await res.json();
      return data.choices[0].message.content.trim();
    }

    const body = await res.text();

    if (res.status === 429 && attempt < MAX_RETRIES) {
      // Parse wait time from Groq error message ("try again in X.XXs")
      const match = body.match(/try again in (\d+(?:\.\d+)?)s/i);
      const waitMs = match ? Math.ceil(parseFloat(match[1]) * 1000) + 500 : (attempt + 1) * 8000;
      console.log(`[groq] Rate limited — waiting ${(waitMs/1000).toFixed(1)}s (attempt ${attempt+1}/${MAX_RETRIES})`);
      await new Promise(r => setTimeout(r, waitMs));
      attempt++;
      continue;
    }

    throw new Error(`Groq API error ${res.status}: ${body}`);
  }
}
