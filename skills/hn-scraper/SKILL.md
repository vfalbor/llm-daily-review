# SKILL: hn-scraper

## Purpose
Fetch the top 30 links from Hacker News front page (https://news.ycombinator.com/)
without clicking "More". Return structured data for each item.

## Trigger
- Orchestrator calls this skill daily at 15:00
- Can also be called manually for testing

## Input
```json
{ "max_items": 30 }
```

## Output
```json
[
  {
    "rank": 1,
    "title": "Show HN: FastEval – open LLM benchmark runner",
    "url": "https://github.com/...",
    "hn_url": "https://news.ycombinator.com/item?id=...",
    "points": 312,
    "comments": 87,
    "author": "username",
    "age": "3 hours ago",
    "scraped_at": "2025-01-15T15:00:00Z"
  }
]
```

## Implementation notes
- Parse `https://news.ycombinator.com/` directly; do NOT follow "More" links
- Respect HN rate limits: one request, no retries within 60s
- Strip tracking parameters from URLs
- If fetch fails, log error and return empty array (do not crash orchestrator)
- Minimum fields required: title, url, rank

## Community adaptation notes
This skill can be extended to:
- Support other sources (Product Hunt, Reddit r/MachineLearning, etc.)
- Add RSS feed parsing as a fallback
- Include comment sentiment as a signal
