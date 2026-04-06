// src/filter/llm-filter.js
// Uses Claude to classify HN items as LLM-related or not,
// and enriches each match with app type and proposed tests.

import { callGroq } from '../llm/groq-adapter.js';

export async function filterLLMApps(items) {
  const prompt = buildClassificationPrompt(items);

  const raw = await callGroq(
    'You are an expert AI/ML tool classifier. You receive a list of Hacker News items and must identify which ones are applications or systems directly related to LLMs, AI agents, or generative AI. Return ONLY valid JSON, no markdown fences.',
    prompt,
    4096
  );
  const text = raw.replace(/^```json\n?|```$/g, '');

  let classified;
  try {
    classified = JSON.parse(text);
  } catch {
    throw new Error('Groq returned invalid JSON for classification');
  }

  // Enrich matched items with classification data
  return classified
    .filter(c => c.is_llm_related)
    .map(c => {
      const original = items.find(i => i.rank === c.rank) || {};
      return { ...original, ...c };
    });
}

function buildClassificationPrompt(items) {
  const list = items
    .map(i => `rank:${i.rank} | title:${i.title} | url:${i.url}`)
    .join('\n');

  return `Classify these Hacker News items. For each, output a JSON array where
each element has:
- rank (number, from input)
- is_llm_related (boolean)
- confidence (0.0–1.0)
- app_type (string from taxonomy or null)
- description (1 sentence, or null if not LLM-related)
- use_modes (array of strings, e.g. ["CLI","Python API"])
- similar_tools (array of 2–3 tool names)
- proposed_tests (array of 3–5 concrete test descriptions)
- requires_api_key (boolean)
- is_open_source (boolean or null if unknown)

App type taxonomy:
benchmark-runner | agent-framework | rag-system | prompt-tool |
fine-tuning | model-server | sdk-wrapper | evaluation | 
vector-db | multimodal | code-assistant | data-pipeline | other-llm

Items:
${list}

Return ONLY the JSON array.`;
}
