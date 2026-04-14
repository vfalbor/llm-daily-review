# LLM Daily Review — AI App Reviews from Hacker News

[![Live](https://img.shields.io/badge/Live-tokenstree.eu-2563eb)](https://tokenstree.eu)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Newsletter](https://img.shields.io/badge/Newsletter-subscribe-green)](https://tokenstree.eu/newsletter/)

> **Automated daily testing & scoring of LLM apps posted on Hacker News.**
> Find the best AI tools before everyone else — free, open source, no login required.

**Live portal → [tokenstree.eu](https://tokenstree.eu)**

Every day at 15:00 UTC, this system scrapes Hacker News, finds LLM-related app submissions, tests each one in an **isolated Docker container**, and scores it across **11 criteria** — publishing results with recommendation badges and a weekly Top 5 newsletter.

---

## What it does

```
15:00 UTC daily
  → Scrape HN front page (top 30 items)
  → Filter: LLM / AI agent / generative AI tools only
  → Deduplicate against previously reviewed apps
  → Spin up Docker container per app (sandboxed, isolated)
  → Test: install, run, interact, benchmark
  → Score: 11 weighted criteria → normalized 0-100
  → Publish to tokenstree.eu with badges
  → Friday: Weekly Top 5 newsletter
```

## Recommendation tiers

| Badge | Threshold | Meaning |
|---|---|---|
| ⭐ **Strong candidate** | Score ≥78 AND novelty ≥7 | Genuinely innovative, works well, worth adopting |
| 👀 **Worth watching** | Score ≥57 | Solid project with clear value |
| 🔍 **Niche** | Score 35–56 | Useful for a specific audience |
| ⏭ **Skip** | Score <35 or differentiation ≤3 | Too similar to existing tools, broken, or thin |

## Scoring criteria (11 weighted, normalized to 100)

| Criterion | Weight | What we measure |
|---|---|---|
| **HN Sentiment** | 15% | Points, comments, positive/negative signals from community |
| **Novelty** | 11% | How original is the approach? Real differentiation vs wrappers |
| **Current relevance** | 11% | Fit with 2025-2026 AI landscape and use cases |
| **Differentiation** | 11% | What sets it apart from existing LLM tools? |
| **Performance** | 10% | Speed, reliability from automated benchmarks |
| **Ease of use** | 8% | QA results, UX quality, time-to-value |
| **Ease of integration** | 8% | API quality, SDK, plugin ecosystem |
| **Documentation** | 7% | README quality, examples, guides |
| **Maturity** | 7% | Commit history, open issues, maintenance signals |
| **Community** | 7% | GitHub stars, contributors, activity |
| **System requirements** | 5% | Setup ease, resource demands |

When a criterion is N/A, its weight is redistributed proportionally.

## API

```bash
# Results for a specific date
GET https://tokenstree.eu/api/results?date=2026-04-14

# Calendar data (days with results)
GET https://tokenstree.eu/api/calendar?year=2026&month=4

# Weekly Top 5
GET https://tokenstree.eu/api/weekly-top5
GET https://tokenstree.eu/api/weekly-top5?week=2026-W15
```

## Skills (open source scoring rubrics)

All LLM skills live in `/skills/` — fork and improve them freely.

| Skill | Purpose |
|---|---|
| [`hn-scraper`](skills/hn-scraper/) | Fetch and parse HN front page |
| [`app-identifier`](skills/app-identifier/) | Classify and filter LLM-related apps |
| [`app-scorer`](skills/app-scorer/) | Score apps across 11 criteria |
| [`app-benchmarker`](skills/app-benchmarker/) | Automated performance testing |
| [`weekly-top5`](skills/weekly-top5/) | Friday ranking logic |
| [`newsletter`](skills/newsletter/) | Daily + weekly email generation |

## Running locally

```bash
git clone https://github.com/vfalbor/llm-daily-review
cd llm-daily-review
npm install
cp .env.example .env   # fill in: ANTHROPIC_API_KEY, SMTP credentials, GITHUB_TOKEN
node src/orchestrator/run.js   # run a review cycle
node src/web/server.js         # start the web UI on localhost:3000
```

To set up the daily cron (runs at 15:00 UTC):
```bash
bash cron/setup-cron.sh
```

## Stack

- **Runtime**: Node.js 20 (ESM)
- **Web**: Express + SQLite (better-sqlite3)
- **LLM scoring**: Claude API (Anthropic)
- **Testing**: Docker (isolated containers per app)
- **Email**: Nodemailer
- **Hosting**: Linux VPS + nginx reverse proxy

## Newsletter

Subscribe free at [tokenstree.eu](https://tokenstree.eu):
- **Daily digest**: every tested app with scores
- **Weekly Top 5**: Friday summary of the week's best LLM apps

Sent from `info@tokenstree.com` — check spam on first delivery.

## License

**CC BY 4.0** — fork, adapt, use commercially. Attribution required.
Skills are intentionally designed to be community-adaptable. Fork and submit PRs.

---

*Built with [Claude Code](https://claude.ai/code) · Free forever · [tokenstree.eu](https://tokenstree.eu)*
