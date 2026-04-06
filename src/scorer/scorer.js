// src/scorer/scorer.js
// Calls Claude to score an app across 7 criteria using the app-scorer skill rubrics.

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'llama-3.3-70b-versatile';

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const SKILL_MD = readFileSync(
  join(__dir, '../../skills/app-scorer/SKILL.md'), 'utf8'
);

export async function scoreApp(app, testResults) {
  const prompt = `${SKILL_MD}

---

Now score the following app using the rubrics above.

APP DATA:
${JSON.stringify(app, null, 2)}

TEST RESULTS:
${JSON.stringify(testResults, null, 2)}

Return ONLY valid JSON matching the output schema in the skill.`;

  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.GROQ_API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 2048,
      messages: [
        {
          role: 'system',
          content: 'You are an expert LLM tool evaluator. You score apps rigorously and write concrete, evidence-based justifications. Return ONLY valid JSON, no markdown fences.'
        },
        { role: 'user', content: prompt }
      ],
    }),
  });

  if (!res.ok) throw new Error(`Groq scorer API error: ${res.status} ${await res.text()}`);
  const data = await res.json();
  const text = data.choices[0].message.content.trim().replace(/^```json\n?|```$/g, '');

  const scored = JSON.parse(text);
  scored.scored_at = new Date().toISOString();
  scored.app_url = app.url;

  // Compute total score
  scored.total_score = Object.values(scored.scores).reduce(
    (sum, s) => sum + (s.score || 0), 0
  );

  return scored;
}
