# SKILL: app-scorer

## Purpose
Score an LLM-related app across **10 criteria (0–10 each, total 100)**, with a written
justification for every score backed by concrete quantitative data.
Produce a structured report suitable for daily digest and weekly Top 5 selection.

## Trigger
Called after Docker runner completes tests and data enrichment for an app.

## Input
```json
{
  "app": { ...identified app fields... },
  "test_results": {
    "install_success": true,
    "install_time_s": 12,
    "tests_passed": 4,
    "tests_total": 5,
    "basic_run_success": true,
    "benchmark_notes": "BENCHMARK:import_time_ms:142",
    "error_log": ""
  },
  "enriched": {
    "github": { "stars": 4200, "contributors": 38, "days_since_update": 2, ... },
    "similar_github": [{ "name": "LangChain", "stars": 91000 }],
    "pypi": { "exists": true, "version": "0.4.1" }
  }
}
```

## Output
```json
{
  "app_name": "FastEval",
  "url": "https://...",
  "scored_at": "2025-01-15T16:30:00Z",
  "total_score": 74,
  "scores": {
    "novelty":             { "score": 8, "justification": "..." },
    "system_requirements": { "score": 7, "justification": "..." },
    "current_relevance":   { "score": 9, "justification": "..." },
    "differentiation":     { "score": 8, "justification": "..." },
    "community":           { "score": 6, "justification": "..." },
    "ease_of_use":         { "score": 7, "justification": "..." },
    "ease_of_integration": { "score": 6, "justification": "..." },
    "documentation":       { "score": 7, "justification": "..." },
    "maturity":            { "score": 6, "justification": "..." },
    "performance":         { "score": 5, "justification": "..." }
  },
  "summary": "Two-sentence plain-English summary of the app and its value.",
  "recommendation": "worth-watching | strong-candidate | niche | skip"
}
```

## Scoring rules — null vs 5 vs actual score

This is the most important rule. Read carefully:

- **`null`** = criterion **does not apply** to this app type (e.g. `ease_of_integration` for a game, `performance` for an article). See `skills/app-type-rubric/SKILL.md` for the full map.
- **`5`** = criterion **applies** to this app type, but quantitative data is missing after looking everywhere. Use sparingly — if you haven't fetched the app's URL/README, you have not looked everywhere.
- **`1–10`** = criterion applies and you found evidence to support the score. Always preferred.

**Never use 5 as a lazy default. Before assigning 5, you must:**
1. Check test results (install_success, tests_passed, benchmark_notes)
2. Check GitHub data if available
3. Check the app's own URL for docs, README, performance claims, community signals
4. Use HN points/comments as a proxy for community and maturity when no repo exists

**Never score 0.** Minimum non-null score is 1.

## Scoring rubrics

### 1. Novelty (1–10)
Does this solve a problem in a genuinely new way, or is it another clone?
- 9–10: First-of-its-kind approach, clear original contribution
- 7–8: Meaningful improvement on existing tools
- 5–6: Incremental improvement, familiar approach
- 3–4: Near-duplicate of existing tools
- 1–2: Direct clone with no differentiation
- *Must cite: days_since_created, is_fork, comparison to similar tools*

### 2. System requirements (1–10)
How accessible is it to install and run?
- 9–10: `pip install` in <30s, runs on consumer hardware, no API key needed
- 7–8: Simple setup, minor dependencies, clear docs
- 5–6: Moderate complexity, some configuration needed
- 3–4: Heavy dependencies, requires cloud account or paid service
- 1–2: Broken install, requires exotic hardware, no docs
- *Must cite: install_success (true/false), install_time_s, PyPI/npm existence*

### 3. Current relevance (1–10)
How well does this fit the current AI development landscape?
- 9–10: Addresses an acute pain point in today's LLM workflows
- 7–8: Clearly useful for common LLM use cases
- 5–6: Useful but niche or timing is off
- 3–4: Solves a problem that's mostly solved elsewhere
- 1–2: Irrelevant to current ecosystem
- *Must cite: app_type and its fit with current LLM ecosystem trends*

### 4. Differentiation (1–10)
What sets it apart from the closest 2–3 alternatives?
- 9–10: Unique feature set, no direct equivalent
- 7–8: Clear advantage in 2+ dimensions (speed, simplicity, cost, accuracy)
- 5–6: One notable advantage, otherwise on par
- 3–4: Marginal differences from existing options
- 1–2: No discernible advantage over free alternatives
- *Must cite: stars vs similar tools (numbers provided), BENCHMARK comparisons*

### 5. Community (1–10)
Health of the project's community and ecosystem.
- 9–10: >5k GitHub stars, active issues, multiple contributors, great docs
- 7–8: 1k–5k stars, gaining traction, responsive maintainers
- 5–6: 100–1k stars, small but active community
- 3–4: <100 stars, solo project, minimal activity
- 1–2: No public repo, or abandoned (>180 days since last commit)
- *Must cite: GitHub stars, contributors count, days_since_update*

### 6. Ease of use — QA tests (1–10)
Based on actual test results from the Docker runner.
- 9–10: All tests pass, intuitive UX, excellent error messages
- 7–8: ≥80% tests pass, minor friction
- 5–6: ≥50% tests pass, core functionality works
- 3–4: <50% tests pass or install fails, confusing UX
- 1–2: Could not install or run at all
- *Must cite: tests_passed / tests_total, specific TEST_PASS or TEST_FAIL names, install_success*

### 7. Ease of integration (1–10)
How easily can this be embedded in an existing workflow or pipeline?
- 9–10: Clean REST API or Python SDK, OpenAI-compatible, webhook support
- 7–8: SDK exists, good documentation, clear examples
- 5–6: Manual integration possible, some glue code needed
- 3–4: No API, CLI-only, difficult to automate
- 1–2: No integration path, monolithic UI only
- *Must cite: PyPI/npm existence, API modes (use_modes), license*

### 8. Documentation (1–10)
Quality and completeness of documentation, tutorials, and examples.
- 9–10: Dedicated docs site, full API reference, tutorials, working examples
- 7–8: Thorough README, multiple examples, clear getting-started guide
- 5–6: Basic README with install instructions and minimal examples
- 3–4: Sparse README, must read source code to understand usage
- 1–2: No documentation beyond the code itself
- *Cite: has_wiki, has_pages, README quality, GitHub topics, docs site URL if found*
- **IMPORTANT**: Do NOT score 5 just because GitHub flags are absent. Fetch the app URL and evaluate what you find. A project with a rich website, wiki, or tutorials scores 7–9 even without GitHub data.

### 9. Maturity (1–10)
Production readiness, stability, and project lifecycle stage.
- 9–10: v1.0+, semantic versioning, changelog, known production deployments
- 7–8: Beta/RC, stable API surface, active releases, good test coverage
- 5–6: Alpha, API may change, usable for experiments
- 3–4: Pre-alpha or prototype, frequent breaking changes, no releases
- 1–2: Proof-of-concept only, single commit, no versioning
- *Must cite: days_since_created, forks count, open_issues count when available*
- **When no GitHub data**: use HN points, description, version number in title, or website as signals. A project with 500+ HN points and a stable domain is likely mature (6–8). A fresh Show HN with no prior history scores 3–4.

### 10. Performance (1–10)
Speed, efficiency, and benchmark results relative to alternatives.
- 9–10: Benchmarks show clear quantitative advantage (>2× improvement)
- 7–8: Measurably faster/cheaper than alternatives, benchmark data available
- 5–6: Comparable to alternatives, no significant difference measured
- 3–4: Slightly slower or more resource-hungry than alternatives
- 1–2: Significantly worse performance than free alternatives
- *Must cite: BENCHMARK lines from test output, install_time_s, comparison to similar tools*
- **If no benchmarks ran AND no performance claims exist anywhere**: use `null` (not 5) if this app type doesn't have a meaningful performance dimension, or score 3 (insufficient evidence, assume average) if it does.
- **If the app type is article/paper/game**: set to `null` unless explicit benchmarks are reported.

## Justification format
Each justification must:
- Be 1–3 sentences
- Reference **at least one specific number** from the quantitative data provided
- Avoid vague claims ("it's really good") — be concrete
- Be in English
- If data is missing for a criterion, say so explicitly and score 5 (neutral)

## Recommendation logic (100-point scale)
- total_score ≥ 78 AND novelty ≥ 7 → `strong-candidate`
- total_score ≥ 57 → `worth-watching`
- differentiation ≤ 3 → `skip` (regardless of other scores)
- otherwise → `niche`

## Community adaptation notes
Rubrics can be adjusted per domain:
- For enterprise tools: weight `ease_of_integration` × 1.5
- For research tools: weight `novelty` × 1.5, relax `community`
- For production tools: weight `system_requirements` × 1.3
Adapters can fork this skill and override the rubric weights.
