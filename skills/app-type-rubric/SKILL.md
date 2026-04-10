# SKILL: app-type-rubric

## Purpose
Map each app type to the criteria that apply, those that are N/A, and how to
interpret ambiguous criteria. Used by the scorer before assigning scores so that
`null` (does not apply) is never confused with `5` (applies but data is missing).

---

## Critical distinction

| Value | Meaning | When to use |
|---|---|---|
| `null` | Criterion **does not apply** to this type of app | Integration for a game; performance for an article |
| `5` | Criterion **applies** but quantitative data is missing | Maturity of a GitHub repo with no release tags |
| `1–4` or `6–10` | Criterion applies and evidence supports the score | Always preferred over defaulting to 5 |

**Never use 5 as a lazy default. If the criterion applies, find evidence in the app URL, HN post, description, or test results and score accordingly.**

---

## App type definitions and rubric adaptations

### `llm-tool` / `llm-ai`
LLM wrappers, agents, evaluation frameworks, fine-tuning tools, prompt libraries.
- All 11 criteria apply.
- `performance`: if no benchmarks ran, fetch README for any stated benchmark claims. Score 5 only if no claims exist anywhere.
- `documentation`: fetch the project URL and assess README/docs site quality directly. Do NOT default to 5 because GitHub flags are missing.

### `devtool`
Developer tools, IDEs, linters, code generators, CI/CD tools.
- All criteria apply.
- `current_relevance`: assess fit with the developer tooling landscape, not LLM trends.
- `performance`: relevant — assess build times, latency, throughput from any available data.

### `database` / `data`
Databases, data pipelines, analytics tools.
- All criteria apply.
- `performance`: critical criterion — assess read/write benchmarks. Score 3 if no benchmark data rather than 5.
- `ease_of_integration`: assess via available client libraries and API surface.

### `infrastructure` / `security`
Infra tools, monitoring, deployment, security scanners.
- All criteria apply.
- `ease_of_use`: score based on deployment complexity, not UX aesthetics.
- `performance`: assess resource overhead; use 3 if no data rather than 5.

### `library` / `framework`
Reusable libraries, SDKs, language frameworks.
- All criteria apply.
- `ease_of_integration`: primary criterion — weight it heavily in justification.
- `documentation`: fetch the library's docs site. A library without good docs scores 2–3, not 5.
- `community`: GitHub stars and contributors are reliable signals here.

### `game`
Games, interactive experiences, game engines.
- `ease_of_integration` → **null** (N/A — games are not integrated into pipelines)
- `performance`: assess frame rate, load time if mentioned; otherwise **null**
- `current_relevance`: score based on novelty in the game/interactive space, not LLM trends
- `ease_of_use`: score based on accessibility (platform support, controls, learning curve)
- `documentation`: score based on README, wiki, or website quality. Fetch the URL.

### `research` / `paper`
Academic papers, research publications, experiment reports.
- `ease_of_integration` → **null**
- `ease_of_use` → **null** (papers are read, not installed)
- `system_requirements` → **null**
- `performance`: score only if the paper reports benchmark results. Otherwise **null**.
- `novelty`: primary criterion — assess the research contribution directly.
- `documentation`: score the quality of the paper/abstract itself (1=poor, 10=excellent).
- `community`: assess via citation count, HN points, author reputation if available. Use HN points as proxy if nothing else.
- `maturity`: score based on whether it has a code release, reproducibility. Not age.

### `article` / `tutorial` / `blog`
Articles, tutorials, blog posts, educational content.
- `ease_of_integration` → **null**
- `ease_of_use` → **null**
- `system_requirements` → **null**
- `performance` → **null**
- `maturity` → **null**
- `novelty`: assess how original the insight or teaching approach is.
- `documentation`: score the clarity and depth of the writing itself.
- `community`: use HN points and comments as the primary signal.
- `differentiation`: how different is this from existing tutorials/articles on the same topic?

### `web-app` / `saas`
Web applications, SaaS products, hosted tools.
- `system_requirements`: score based on whether it requires signup, payment, or setup. Pure web = 9–10.
- `ease_of_integration`: score based on API availability, webhooks, embeds.
- `performance`: assess page load, response time if mentioned. Otherwise **null**.
- `documentation`: fetch the product's website and assess it directly.
- `maturity`: use pricing page, about page, or HN comments about production use as signals.

### `hardware` / `embedded`
Hardware projects, embedded systems, firmware.
- `ease_of_integration` → score based on standard interfaces (I2C, USB, GPIO). Not software integration.
- `performance` → assess based on specs mentioned (speed, power, latency).
- `system_requirements` → assess required hardware cost and availability.
- `documentation`: fetch the project page; hardware projects often have schematics and build guides.

### `language` / `compiler`
Programming languages, compilers, interpreters, runtimes.
- All criteria apply.
- `current_relevance`: assess fit with current language ecosystem trends.
- `performance`: critical — any benchmark vs existing languages should be cited.
- `documentation`: language reference, tutorials, stdlib docs are key signals.

---

## Using this rubric in the scorer

Before scoring, identify the `app_type` and:
1. Set any N/A criteria to `null` with justification "N/A for this app type"
2. For criteria where no data exists but the criterion APPLIES, fetch the app URL and look for evidence before defaulting to 5
3. When scoring community/maturity without GitHub data, use HN points, comments, and post age as proxy signals:
   - HN points > 500: community score 7–8
   - HN points 200–500: community score 5–6
   - HN points 50–200: community score 3–4
   - HN points < 50: community score 1–2
4. For documentation without GitHub data: fetch the URL and score the docs/README quality directly
