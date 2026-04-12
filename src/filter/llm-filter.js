// src/filter/llm-filter.js
// Uses the app-identifier skill (skills/app-identifier/SKILL.md) via Groq
// to classify ALL HN items — not just LLM apps — and propose type-specific benchmarks.
// Covers devtools, databases, languages, security, infrastructure, research, and more.
// For articles/posts, also fetches the page to extract the real tool URL.
//
// Batches items (BATCH_SIZE=10) to stay within Groq TPM limits.

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { llmCall, GROQ_MODEL_FAST } from '../llm/index.js';

const __dir = dirname(fileURLToPath(import.meta.url));
const SKILL_MD = readFileSync(join(__dir, '../../skills/app-identifier/SKILL.md'), 'utf8');

// Send items in batches to stay under Groq TPM limits
// (SKILL.md is ~2k tokens, 10 items ~300 tokens, response ~1k tokens → ~3.3k total, safe under 6k)
const BATCH_SIZE = 10;

// Patterns that suggest a URL is a direct tool/repo, not an article
const TOOL_URL_PATTERNS = [
  /github\.com\/[^/]+\/[^/]+/,
  /gitlab\.com\/[^/]+\/[^/]+/,
  /npmjs\.com\/package\//,
  /pypi\.org\/project\//,
  /crates\.io\/crates\//,
  /pkg\.go\.dev\//,
  /huggingface\.co\//,
  /hub\.docker\.com\//,
];

function looksLikeTool(url) {
  return TOOL_URL_PATTERNS.some(p => p.test(url));
}

// Fetch a page and extract the first known tool registry URL found in it
async function extractToolUrlFromPage(url) {
  try {
    const res = await fetch(url, {
      signal: AbortSignal.timeout(6000),
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; HNReviewer/1.0)' },
    });
    if (!res.ok) return null;
    const html = await res.text();

    const patterns = [
      /https?:\/\/github\.com\/([a-zA-Z0-9_-]+\/[a-zA-Z0-9_.-]+)(?:['"?\s])/,
      /https?:\/\/gitlab\.com\/([a-zA-Z0-9_-]+\/[a-zA-Z0-9_.-]+)(?:['"?\s])/,
      /https?:\/\/pypi\.org\/project\/([a-zA-Z0-9_-]+)(?:['"?\s/])/,
      /https?:\/\/npmjs\.com\/package\/([a-zA-Z0-9_@/-]+)(?:['"?\s])/,
      /https?:\/\/crates\.io\/crates\/([a-zA-Z0-9_-]+)(?:['"?\s])/,
    ];
    const bases = [
      'https://github.com/',
      'https://gitlab.com/',
      'https://pypi.org/project/',
      'https://npmjs.com/package/',
      'https://crates.io/crates/',
    ];

    for (let i = 0; i < patterns.length; i++) {
      const matches = [...html.matchAll(new RegExp(patterns[i].source, 'g'))];
      for (const m of matches) {
        const candidate = bases[i] + m[1].replace(/\.git$/, '');
        // Validate the URL actually exists before returning it
        try {
          const check = await fetch(candidate, {
            method: 'HEAD',
            signal: AbortSignal.timeout(4000),
            headers: { 'User-Agent': 'Mozilla/5.0 (compatible; HNReviewer/1.0)' },
          });
          if (check.ok) return candidate;
        } catch { /* try next match */ }
      }
    }
    return null;
  } catch {
    return null;
  }
}

async function classifyBatch(batch) {
  const list = batch
    .map(i => `rank:${i.rank} | title:${i.title} | url:${i.url}`)
    .join('\n');

  const userPrompt = `${SKILL_MD}

---

Apply the skill above to classify the following Hacker News items.
Return a JSON array — one object per item — with ALL fields from the Output schema.
For is_reviewable=false items, set is_reviewable:false and null for other fields.
Return ONLY the JSON array, no markdown fences.

Items:
${list}`;

  const raw = await llmCall(
    'You are an expert HN app classifier. Identify reviewable tools, libraries, apps, and projects across ALL tech domains — not just LLM/AI. Return ONLY valid JSON array, no markdown fences.',
    userPrompt,
    2048,
    GROQ_MODEL_FAST
  );

  return JSON.parse(raw.replace(/^```json\n?|```$/gm, '').trim());
}

export async function filterLLMApps(items) {
  // Split into batches
  const batches = [];
  for (let i = 0; i < items.length; i += BATCH_SIZE) {
    batches.push(items.slice(i, i + BATCH_SIZE));
  }

  // Process batches sequentially (avoid concurrent TPM pressure)
  const classified = [];
  for (const batch of batches) {
    try {
      const results = await classifyBatch(batch);
      classified.push(...results);
    } catch (err) {
      // If a batch fails, log and continue — don't crash the whole run
      console.error(`[WARN] Batch classification failed: ${err.message}`);
    }
  }

  // Keep all reviewable items
  const candidates = classified
    .filter(c => c.is_reviewable)
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
            app.tool_url = extracted;
            app.repo_url = extracted;
          }
        }
      }
      if (!app.tool_url && looksLikeTool(app.url)) {
        app.tool_url = app.url;
      }
    })
  );

  return candidates;
}
