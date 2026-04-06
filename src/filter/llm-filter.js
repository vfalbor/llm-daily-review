// src/filter/llm-filter.js
// Uses the app-identifier skill (skills/app-identifier/SKILL.md) via Groq
// to classify HN items and propose type-specific QA benchmarks.
// For articles/posts, also fetches the page to extract the real tool URL.

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { callGroq, GROQ_MODEL_FAST } from '../llm/groq-adapter.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const SKILL_MD = readFileSync(join(__dir, '../../skills/app-identifier/SKILL.md'), 'utf8');

// Patterns that suggest a URL is a direct tool/repo, not an article
const TOOL_URL_PATTERNS = [
  /github\.com\/[^/]+\/[^/]+/,
  /npmjs\.com\/package\//,
  /pypi\.org\/project\//,
  /huggingface\.co\//,
  /gitlab\.com\/[^/]+\/[^/]+/,
];

function looksLikeTool(url) {
  return TOOL_URL_PATTERNS.some(p => p.test(url));
}

// Fetch a page and extract the first GitHub repo URL found in it
async function extractToolUrlFromPage(url) {
  try {
    const res = await fetch(url, {
      signal: AbortSignal.timeout(6000),
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; HNReviewer/1.0)' },
    });
    if (!res.ok) return null;
    const html = await res.text();

    // Find first GitHub repo link (owner/repo pattern, not github.com itself)
    const ghMatch = html.match(/https?:\/\/github\.com\/([a-zA-Z0-9_-]+\/[a-zA-Z0-9_.-]+)(?:['"?\s])/);
    if (ghMatch) {
      return `https://github.com/${ghMatch[1].replace(/\.git$/, '')}`;
    }
    return null;
  } catch {
    return null;
  }
}

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
    4096,
    GROQ_MODEL_FAST   // classification only needs fast/cheap model
  );

  let classified;
  try {
    classified = JSON.parse(raw.replace(/^```json\n?|```$/gm, '').trim());
  } catch {
    throw new Error('Groq returned invalid JSON for classification');
  }

  const candidates = classified
    .filter(c => c.is_llm_related)
    .map(c => {
      const original = items.find(i => i.rank === c.rank) || {};
      return { ...original, ...c };
    });

  // For articles without a tool_url: try to extract one by fetching the page
  await Promise.all(
    candidates.map(async app => {
      if (app.source_type === 'article' || app.source_type === 'tutorial') {
        if (!app.tool_url && !looksLikeTool(app.url)) {
          const extracted = await extractToolUrlFromPage(app.url);
          if (extracted) {
            app.tool_url  = extracted;
            app.repo_url  = extracted;
          }
        }
      }
      // If tool_url not set but url is a direct tool, mirror it
      if (!app.tool_url && looksLikeTool(app.url)) {
        app.tool_url = app.url;
      }
    })
  );

  return candidates;
}
