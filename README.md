# LLM Daily Review

> Automated daily discovery and evaluation of LLM-related applications published on Hacker News.

Every day at 15:00, this system scrapes the HN front page, filters LLM-related tools, tests each one in an isolated Docker container, scores it across 11 criteria, and publishes the results — daily report + weekly Top 5.

---

## How it works

1. **Scraper** fetches the top 30 HN links (no pagination)
2. **Identifier skill** filters apps related to LLMs / AI agents
3. **Deduplication** skips apps already evaluated
4. **Docker runner** tests each app in an isolated, minimal container
5. **Scorer skill** rates each app 0–10 on 7 criteria
6. **Report generator** creates daily markdown + web entry
7. **Newsletter** sends daily digest + weekly Top 5 (Fridays)

## Scoring criteria (11 weighted, normalized to 100)

| Criterion | Weight | Description |
|---|---|---|
| **HN Sentiment** | 15% | Community reception on Hacker News — points, comments, positive/negative signals |
| **Novelty** | 11% | How new or original is the approach? |
| **Current relevance** | 11% | Fit with the current AI landscape |
| **Differentiation** | 11% | What sets it apart from similar tools? |
| **Performance** | 10% | Benchmark results from automated tests |
| **Ease of use** | 8% | QA test results; UX quality |
| **Ease of integration** | 8% | API, SDK, plugin ecosystem |
| **Documentation** | 7% | Wiki, pages, topics, written clarity |
| **Maturity** | 7% | Age, forks, open issues |
| **Community** | 7% | Stars, contributors, activity |
| **System requirements** | 5% | Ease of setup; resource demands |

Each criterion is scored 0–10 by the LLM. The final score is weighted and normalized to 100. When a criterion is N/A, its weight is redistributed among the active criteria.

## Skills

All skills live in `/skills/` and are public. The community can fork and improve them.

| Skill | Purpose |
|---|---|
| `hn-scraper` | Fetch and parse HN front page |
| `app-identifier` | Classify apps and filter LLM-related ones |
| `app-scorer` | Score apps across 11 criteria |
| `weekly-top5` | Friday ranking logic |
| `newsletter` | Daily + weekly email generation |

## Running locally

```bash
npm install
cp .env.example .env   # fill in SMTP + GitHub credentials
node src/orchestrator/run.js
```

To set up the daily cron:
```bash
bash cron/setup-cron.sh
```

## Contributing

This project is open under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.
Skills are intentionally designed to be community-adaptable. Fork, improve, and submit a PR.

## Newsletter

Subscribe at [tokenstree.com](https://tokenstree.com) — daily and weekly editions available.
Sent from **info@tokenstree.com** — check your spam folder on the first delivery.

---

*Built with Claude Code · Published on GitHub · Free forever*
