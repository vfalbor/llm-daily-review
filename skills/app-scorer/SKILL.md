# SKILL: app-scorer

## Purpose
Score an LLM-related app across 7 criteria (0–10 each), with a written
justification for every score. Produce a structured report suitable for
daily digest and weekly Top 5 selection.

## Trigger
Called after Docker runner completes tests for an app.

## Input
```json
{
  "app": { ...identified app fields... },
  "test_results": {
    "install_success": true,
    "install_time_s": 12,
    "basic_run_success": true,
    "error_log": "",
    "notes": "All tests passed. Docs clear."
  }
}
```

## Output
```json
{
  "app_name": "FastEval",
  "url": "https://...",
  "scored_at": "2025-01-15T16:30:00Z",
  "total_score": 61,
  "scores": {
    "novelty": { "score": 8, "justification": "..." },
    "system_requirements": { "score": 7, "justification": "..." },
    "current_relevance": { "score": 9, "justification": "..." },
    "differentiation": { "score": 8, "justification": "..." },
    "community": { "score": 6, "justification": "..." },
    "ease_of_use": { "score": 7, "justification": "..." },
    "ease_of_integration": { "score": 6, "justification": "..." }
  },
  "summary": "Two-sentence plain-English summary of the app and its value.",
  "recommendation": "worth-watching | strong-candidate | niche | skip"
}
```

## Scoring rubrics

### 1. Novelty (0–10)
Does this solve a problem in a genuinely new way, or is it another clone?
- 9–10: First-of-its-kind approach, clear original contribution
- 7–8: Meaningful improvement on existing tools
- 5–6: Incremental improvement, familiar approach
- 3–4: Near-duplicate of existing tools
- 0–2: Direct clone with no differentiation

### 2. System requirements (0–10)
How accessible is it to install and run?
- 9–10: `pip install` or single Docker command, runs on consumer hardware
- 7–8: Simple setup, minor dependencies, clear docs
- 5–6: Moderate complexity, some configuration needed
- 3–4: Heavy dependencies, requires cloud account or paid service
- 0–2: Broken install, requires exotic hardware, no docs

### 3. Current relevance (0–10)
How well does this fit the current AI development landscape?
- 9–10: Addresses an acute pain point in today's LLM workflows
- 7–8: Clearly useful for common LLM use cases
- 5–6: Useful but niche or timing is off
- 3–4: Solves a problem that's mostly solved elsewhere
- 0–2: Irrelevant to current ecosystem

### 4. Differentiation (0–10)
What sets it apart from the closest 2–3 alternatives?
- 9–10: Unique feature set, no direct equivalent
- 7–8: Clear advantage in 2+ dimensions (speed, simplicity, cost, accuracy)
- 5–6: One notable advantage, otherwise on par
- 3–4: Marginal differences from existing options
- 0–2: No discernible advantage

### 5. Community (0–10)
Health of the project's community and ecosystem.
- 9–10: >1k GitHub stars, active issues, multiple contributors, good docs
- 7–8: Gaining traction, responsive maintainers, decent docs
- 5–6: Small but active community, basic docs
- 3–4: Solo project, minimal docs, slow responses
- 0–2: Abandoned, no docs, no community

### 6. Ease of use — QA tests (0–10)
Based on actual test results from the Docker runner.
- 9–10: All tests pass, intuitive UX, excellent error messages
- 7–8: Most tests pass, minor friction
- 5–6: Core functionality works, rough edges
- 3–4: Multiple test failures, confusing UX
- 0–2: Could not complete basic tests

### 7. Ease of integration (0–10)
How easily can this be embedded in an existing workflow or pipeline?
- 9–10: Clean REST API or Python SDK, OpenAI-compatible, webhook support
- 7–8: SDK exists, good documentation, clear examples
- 5–6: Manual integration possible, some glue code needed
- 3–4: No API, CLI-only, difficult to automate
- 0–2: No integration path, monolithic UI only

## Justification format
Each justification must:
- Be 1–3 sentences
- Reference specific observed evidence (install time, GitHub stats, test result)
- Avoid vague claims ("it's really good") — be concrete
- Be in English

## Recommendation logic
- total_score >= 55 AND novelty >= 7 → `strong-candidate`
- total_score >= 40 → `worth-watching`
- differentiation <= 3 → `skip` (regardless of other scores)
- otherwise → `niche`

## Community adaptation notes
Rubrics can be adjusted per domain:
- For enterprise tools: weight `ease_of_integration` × 1.5
- For research tools: weight `novelty` × 1.5, relax `community`
- For production tools: weight `system_requirements` × 1.3
Adapters can fork this skill and override the rubric weights.
