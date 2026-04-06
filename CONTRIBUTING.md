# Contributing to LLM Daily Review

This project is designed to be adapted and improved by the community.
All skills are in `/skills/` and are intentionally written as plain Markdown
so anyone can read, fork, and improve them without needing to understand the codebase.

## How skills work

Each skill is a `SKILL.md` file that Claude Code reads as a prompt.
Skills define:
- What input they accept
- What output they produce (JSON schema)
- Rules, rubrics, and classification logic
- Community adaptation notes

## Ways to contribute

### 1. Improve a rubric
Open `skills/app-scorer/SKILL.md` and propose a better rubric for one of the 7 criteria.
Example: "The community score should also consider Discord server activity, not just GitHub stars."

### 2. Add a new app type
Open `skills/app-identifier/SKILL.md` and add a new value to the app type taxonomy.
Example: `browser-extension` or `fine-tune-hub`.

### 3. Add a new data source
Fork `skills/hn-scraper/SKILL.md` and create a variant for Reddit, Product Hunt, or X/Twitter.
Skills can be chained — the orchestrator can call multiple scrapers.

### 4. Create a domain-specific scorer
The `app-scorer` skill mentions weight overrides for enterprise, research, or DevOps contexts.
You can create `skills/app-scorer-enterprise/SKILL.md` with custom weights and submit a PR.

### 5. Translate the newsletter
Open `skills/newsletter/SKILL.md` and the templates in `src/email/templates.js`.
All user-facing strings are in English — feel free to add a localised variant.

## Pull request guidelines

- Keep skill changes in `/skills/` separate from code changes in `/src/`
- Skills should remain human-readable Markdown — no code inside SKILL.md
- Add a brief note to SKILL.md explaining why you changed the rubric
- All contributions are published under CC BY 4.0

## Questions?

Open an issue on GitHub or reach out via info@tokenstree.com.
