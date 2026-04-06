# /hn-review — Manual HN LLM Review

Run a full Hacker News LLM app review right now, using Claude Code as the LLM backend (no API key needed).

## Usage
```
/hn-review
/hn-review --date 2025-01-15
/hn-review --dry-run
```

## What this does
1. Scrapes the top 30 items from Hacker News front page
2. Identifies which ones are LLM-related apps/tools
3. Tests each new app in an isolated Docker container
4. Scores them across 7 criteria (0–10 each)
5. Generates a daily report in data/reports/
6. Sends newsletter to subscribers (skip with --dry-run)

## Arguments
- `--date YYYY-MM-DD` — review HN from a specific date (uses live HN, date is for DB/report label only)
- `--dry-run` — run everything but skip sending emails and GitHub upload
- `--no-docker` — skip container tests (score based on metadata only)
- `--limit N` — only process N apps max (default: all found)

## Steps to execute

When this command is run, do the following:

### Step 1 — Set up LLM_PROVIDER
Set the environment so the orchestrator uses Claude Code CLI:
```bash
export LLM_PROVIDER=claude-code
```

### Step 2 — Run the orchestrator
```bash
cd /home/vfalbor/hnreviewer
node src/orchestrator/run.js
```

Watch the logs in real time. The orchestrator will:
- Print each app it finds on HN
- For each LLM-related app: show type, similarity to known tools, proposed tests
- Show scores as they come in (e.g. "FastEval — 58/70 — worth-watching")
- At the end, show the full report path

### Step 3 — View results
```bash
# Latest report
ls -lt data/reports/ | head -5
cat data/reports/$(date +%Y-%m-%d).md

# Check DB
sqlite3 data/review.db "SELECT title, total_score, recommendation FROM tested_apps ORDER BY tested_at DESC LIMIT 10;"
```

### Step 4 — If Friday, run weekly Top 5
The orchestrator does this automatically on Fridays. To force it:
```bash
LLM_PROVIDER=claude-code node -e "
import('./src/scorer/weekly-top5.js').then(m => m.runWeeklyTop5()).then(r => console.log(JSON.stringify(r, null, 2)));
"
```

## Switching providers

To switch back to Groq after this session:
```bash
# Edit .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here

# Restart container
docker restart hnreviewer
```

## Scoring criteria (0–10 each, max 70)
| # | Criterion | What it measures |
|---|---|---|
| 1 | Novelty | Is it genuinely new or a clone? |
| 2 | System requirements | Easy to install and run? |
| 3 | Current relevance | Fits today's LLM ecosystem? |
| 4 | Differentiation | Better than alternatives? |
| 5 | Community | GitHub stars, docs, maintainers |
| 6 | Ease of use | QA test results from Docker |
| 7 | Ease of integration | API/SDK quality |

## Recommendation thresholds
- **strong-candidate** → total ≥ 55 AND novelty ≥ 7
- **worth-watching** → total ≥ 40
- **niche** → everything else
- **skip** → differentiation ≤ 3 (regardless of other scores)

## When to use this skill vs the cron
- **Cron** (15:00 daily) — automated, uses Groq, no interaction needed
- **This skill** — manual trigger, uses your Claude Pro subscription via Claude Code CLI, useful for testing, re-running a day, or when Groq is unavailable
