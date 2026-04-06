// src/scorer/scorer.js
// Scores an app across 10 criteria (0–10 each, total 100) using real quantitative data.
// Every score justification must cite a concrete number from the enrichment data.

import { llmCall } from '../llm/index.js';
import { enrichApp, formatEnrichmentForScorer } from '../enricher/data-enricher.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const SKILL_MD = readFileSync(join(__dir, '../../skills/app-scorer/SKILL.md'), 'utf8');

// Use tool_url (for articles that point to the actual tool) or fall back to app.url
function resolveTestUrl(app) {
  return app.tool_url || app.repo_url || app.url;
}

export async function scoreApp(app, testResults) {
  // Use the real tool URL for enrichment (e.g. when HN post is an article about a tool)
  const enrichTarget = { ...app, url: resolveTestUrl(app) };
  const enriched = await enrichApp(enrichTarget);
  const quantData = formatEnrichmentForScorer(enriched, testResults);

  const prompt = `${SKILL_MD}

---

Score the following app. You MUST base every justification on the quantitative data
provided below. Do not guess or estimate — cite actual numbers.

Rules for justifications (10 criteria, 100 points total):
- novelty MUST cite: days_since_created, is_fork, comparison to similar tools
- system_requirements MUST cite: install_success (true/false), install_time_s, PyPI existence
- current_relevance MUST cite: app_type and its fit with current LLM ecosystem trends
- differentiation MUST cite: stars vs similar tools (numbers provided), BENCHMARK comparisons
- community MUST cite: GitHub stars, contributors count, days_since_update
- ease_of_use MUST cite: tests_passed / tests_total, install_success, specific TEST_PASS or TEST_FAIL names
- ease_of_integration MUST cite: PyPI/npm existence, API modes (use_modes), license
- documentation MUST cite: has_wiki, has_pages, GitHub topics count; score 5 if data unavailable
- maturity MUST cite: days_since_created, forks count, open_issues; score 5 if data unavailable
- performance MUST cite: BENCHMARK lines from tests; score 5 (neutral) if no benchmarks ran

IMPORTANT: Never score any criterion 0. Minimum is 1. Score 5 when data is insufficient.

${quantData}

---

APP METADATA:
- Title: ${app.title}
- URL: ${app.url}${app.tool_url && app.tool_url !== app.url ? `\n- Tool URL (article describes this tool): ${app.tool_url}` : ''}
- Source type: ${app.source_type || 'tool'}
- Type: ${app.app_type}
- Description: ${app.description || ''}
- Use modes: ${(app.use_modes || []).join(', ')}
- Similar tools: ${(app.similar_tools || []).join(', ')}
- Is open source: ${app.is_open_source}
- Requires API key: ${app.requires_api_key}

Return ONLY valid JSON matching the output schema. No markdown fences.`;

  const raw = await llmCall(
    'You are an expert LLM tool evaluator. Score across exactly 10 criteria. Every justification must cite a specific number from the quantitative data. Return ONLY valid JSON, no markdown fences.',
    prompt,
    2048
  );

  const scored = JSON.parse(raw.replace(/^```json\n?|```$/gm, '').trim());
  scored.scored_at   = new Date().toISOString();
  scored.app_url     = app.url;
  scored.tool_url    = app.tool_url || null;
  scored.source_type = app.source_type || 'tool';
  scored.hn_url      = app.hn_url      || null;
  scored.domain      = app.domain      || null;
  scored.app_type    = app.app_type    || null;
  scored.enriched    = {
    github: enriched.github,
    similar_github: enriched.similar_github,
    pypi: enriched.pypi,
    tests_passed: testResults.tests_passed,
    tests_total: testResults.tests_total,
  };

  // Enforce scoring floor: no criterion below 1
  for (const key of Object.keys(scored.scores || {})) {
    if (scored.scores[key].score < 1) scored.scores[key].score = 1;
  }

  scored.total_score = Object.values(scored.scores).reduce(
    (sum, s) => sum + (s.score ?? 0), 0
  );

  // Apply recommendation logic (100-point scale)
  const novelty = scored.scores?.novelty?.score ?? 0;
  const diff    = scored.scores?.differentiation?.score ?? 0;
  if (diff <= 3) {
    scored.recommendation = 'skip';
  } else if (scored.total_score >= 78 && novelty >= 7) {
    scored.recommendation = 'strong-candidate';
  } else if (scored.total_score >= 57) {
    scored.recommendation = 'worth-watching';
  } else {
    scored.recommendation = 'niche';
  }

  return scored;
}
