# SKILL: weekly-top5

## Purpose
Every Friday, select the Top 5 most interesting LLM apps tested during the week.
Produce a ranked report with justifications, suitable for the weekly newsletter.

## Trigger
Orchestrator calls this skill on Fridays after the daily run completes.

## Input
All scored apps from Monday–Friday of the current week (from SQLite).

## Output
```json
{
  "week": "2025-W03",
  "generated_at": "2025-01-17T16:45:00Z",
  "top5": [
    {
      "rank": 1,
      "app_name": "FastEval",
      "url": "https://...",
      "total_score": 61,
      "why_top5": "Ranked first for its unique combination of...",
      "standout_criterion": "novelty",
      "scores_snapshot": { "novelty": 8, "ease_of_use": 7, ... }
    }
  ],
  "honorable_mentions": ["AppX", "AppY"],
  "week_summary": "This week saw a surge in evaluation tooling..."
}
```

## Selection algorithm

### Step 1: Eligibility filter
Remove apps with:
- recommendation == "skip"
- ease_of_use < 4 (broken or untestable)
- total_score < 50 (out of 100)

### Step 2: Weighted ranking
Apply weekly weights to raw scores:

| Criterion | Weight | Source |
|---|---|---|
| novelty | 1.4 | LLM score (0–10) |
| current_relevance | 1.3 | LLM score (0–10) |
| differentiation | 1.3 | LLM score (0–10) |
| hn_sentiment | 1.2 | LLM score derived from comment tone and signals |
| hn_points | 1.1 | Raw HN upvotes at scrape time, normalised to 0–10 against week max |
| performance | 1.2 | LLM score (0–10) |
| ease_of_use | 1.0 | LLM score (0–10) |
| ease_of_integration | 1.0 | LLM score (0–10) |
| documentation | 0.9 | LLM score (0–10) |
| maturity | 0.9 | LLM score (0–10) |
| community | 0.8 | LLM score (0–10) |
| system_requirements | 0.7 | LLM score (0–10) |

weighted_total = sum(score_i × weight_i)

### Step 3: Diversity bonus
If two apps have the same app_type, reduce the lower-ranked one's score by 5%.
Ensures variety across benchmark-runners, agent-frameworks, etc.

### Step 4: Select top 5
Sort by weighted_total DESC, take first 5.

### Step 5: Honorable mentions
Apps ranked 6–8 that scored >= 65 total (out of 100) get an honorable mention.

## Justification format for why_top5
- 2–4 sentences
- Reference the specific criteria that pushed it to the top
- Compare to at least one other app tested this week
- Written in accessible English for a technical-but-not-specialist audience

## Week summary
2–3 sentences describing the week's theme:
- What app_type dominated?
- Any surprising outliers?
- Notable trend in the ecosystem?

## Community adaptation notes
The weight table is the primary lever for adaptation:
- Research community: boost novelty to 2.0
- DevOps community: boost ease_of_integration to 1.8
- Enterprise: boost community and system_requirements
Adapters can define custom weight presets as named profiles.
