// src/scorer/scorer.js
// Scores an app across 7 criteria using real quantitative data:
// GitHub stats, container test results, benchmarks vs similar tools.
// Every score justification must cite a concrete number.

import { callGroq } from '../llm/groq-adapter.js';
import { enrichApp, formatEnrichmentForScorer } from '../enricher/data-enricher.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dir = dirname(fileURLToPath(import.meta.url));
const SKILL_MD = readFileSync(join(__dir, '../../skills/app-scorer/SKILL.md'), 'utf8');

export async function scoreApp(app, testResults) {
  // Fetch real quantitative data first
  const enriched = await enrichApp(app);
  const quantData = formatEnrichmentForScorer(enriched, testResults);

  const prompt = `${SKILL_MD}

---

Score the following app. You MUST base every justification on the quantitative data
provided below. Do not guess or estimate — cite actual numbers.

Rules for justifications:
- community score MUST cite: GitHub stars, contributors, days since last commit
- system_requirements MUST cite: install_time_s, install_success (true/false), PyPI existence
- ease_of_use MUST cite: tests_passed / tests_total, specific TEST_PASS or TEST_FAIL names
- differentiation MUST cite: stars vs similar tools (numbers provided), BENCHMARK comparisons
- novelty MUST cite: days_since_created, is_fork, comparison to similar tools
- current_relevance: cite app_type and its fit with current LLM ecosystem trends
- ease_of_integration MUST cite: PyPI/npm existence, API modes (from use_modes), license

${quantData}

---

APP METADATA:
- Title: ${app.title}
- URL: ${app.url}
- Type: ${app.app_type}
- Description: ${app.description || ''}
- Use modes: ${(app.use_modes || []).join(', ')}
- Similar tools: ${(app.similar_tools || []).join(', ')}
- Is open source: ${app.is_open_source}
- Requires API key: ${app.requires_api_key}

Return ONLY valid JSON matching the output schema. No markdown fences.`;

  const raw = await callGroq(
    'You are an expert LLM tool evaluator. Every score justification must cite a specific number from the quantitative data provided. Return ONLY valid JSON, no markdown fences.',
    prompt,
    2048
  );

  const scored = JSON.parse(raw.replace(/^```json\n?|```$/gm, '').trim());
  scored.scored_at   = new Date().toISOString();
  scored.app_url     = app.url;
  scored.enriched    = {
    github: enriched.github,
    similar_github: enriched.similar_github,
    pypi: enriched.pypi,
    tests_passed: testResults.tests_passed,
    tests_total: testResults.tests_total,
  };

  scored.total_score = Object.values(scored.scores).reduce(
    (sum, s) => sum + (s.score ?? 0), 0
  );

  return scored;
}
