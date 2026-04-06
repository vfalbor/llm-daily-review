# SKILL: newsletter

## Purpose
Generate daily and weekly newsletter emails in clean HTML, ready to send
from info@tokenstree.com via SMTP.

## Editions

### Daily newsletter
Sent every day after the daily run completes.
Subject: `[LLM Daily] {N} new apps tested — {weekday}, {date}`

### Weekly newsletter (Fridays only)
Sent after the Top 5 skill runs.
Subject: `[LLM Weekly] Top 5 LLM apps this week — Week {N}`

## Input (daily)
```json
{
  "edition": "daily",
  "date": "2025-01-15",
  "apps_tested": [ ...scored app objects... ],
  "apps_skipped_dedup": 3
}
```

## Input (weekly)
```json
{
  "edition": "weekly",
  "week": "2025-W03",
  "top5": [ ...top5 objects... ],
  "week_summary": "...",
  "total_apps_tested_week": 18
}
```

## Output
```json
{
  "subject": "...",
  "html_body": "<html>...</html>",
  "plain_text_body": "...",
  "recipients_daily": ["..."],
  "recipients_weekly": ["..."]
}
```

## Email structure — daily
1. Header with date and logo/wordmark
2. "Today we tested N apps" + quick stats
3. One card per app:
   - Name + link
   - Score bar (visual 0–70)
   - Recommendation badge
   - 2-line summary
   - Top 3 scores highlighted
4. Footer: unsubscribe link, spam notice, GitHub link

## Email structure — weekly
1. Header: "LLM Week in Review"
2. Week summary paragraph
3. #1 app — full card with all 7 scores
4. #2–#5 — compact cards
5. Honorable mentions — list
6. Footer

## Design guidelines
- Max width 600px
- White background, dark text — no dark-mode email hacks
- Score bars: colored div, width proportional to score (green >= 7, amber 5–6, red < 5)
- Fonts: system stack (Arial, Helvetica, sans-serif)
- All links must use absolute URLs
- No JavaScript (email clients strip it)
- Include plain text fallback

## Spam mitigation notice
Include this notice in the footer:
> "This email was sent from info@tokenstree.com. If it landed in spam, please
> mark it as safe — we're a new sender and email providers may flag us initially."

## Unsubscribe
Link to `https://tokenstree.com/unsubscribe?token={subscriber_token}`
Must work without JavaScript.

## Community adaptation notes
- Replace branding variables (logo, domain, color scheme)
- Add new section types (e.g., "Community picks", "Upcoming releases")
- Translate to other languages by replacing all string literals
