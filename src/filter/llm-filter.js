// src/filter/llm-filter.js
// Uses the app-identifier skill (skills/app-identifier/SKILL.md) via Groq
// to classify HN items and propose type-specific QA benchmarks.

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { callGroq } from '../llm/groq-adapter.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const SKILL_MD = readFileSync(join(__dir, '../../skills/app-identifier/SKILL.md'), 'utf8');

export async function filterLLMApps(items) {
  const list = items
    .map(i => `rank:${i.rank} | title:${i.title} | url:${i.url}`)
    .join('\n');

  const userPrompt = `${SKILL_MD}

---

Apply the skill above to classify the following Hacker News items.
Return a JSON array — one object per item — with ALL fields from the Output schema.
For is_llm_related=false items, you may use null for most fields.
Return ONLY the JSON array, no markdown fences.

Items:
${list}`;

  const raw = await callGroq(
    'You are an expert AI/ML tool classifier. Follow the skill definition exactly. Return ONLY valid JSON, no markdown fences.',
    userPrompt,
    4096
  );

  let classified;
  try {
    classified = JSON.parse(raw.replace(/^```json\n?|```$/gm, '').trim());
  } catch {
    throw new Error('Groq returned invalid JSON for classification');
  }

  return classified
    .filter(c => c.is_llm_related)
    .map(c => {
      const original = items.find(i => i.rank === c.rank) || {};
      return { ...original, ...c };
    });
}
