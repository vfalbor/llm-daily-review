# SKILL: app-identifier

## Purpose
Given a list of HN items, identify which ones describe a **reviewable app, tool,
library, framework, or project** — regardless of tech domain. HN publishes everything
from LLM frameworks to new programming languages, databases, hardware projects, and
devtools. This skill classifies all of them.

For each match, extract the actual tool URL, classify the type, identify similar tools,
and propose QA benchmarks appropriate for the app type.

## Trigger
Called by orchestrator after hn-scraper, receives raw item list.

## Input
```json
[{ "title": "...", "url": "...", "rank": 1 }]
```

## Output
```json
[
  {
    "rank": 1,
    "title": "Turso – SQLite for production",
    "url": "https://turso.tech",
    "tool_url": "https://github.com/tursodatabase/libsql",
    "source_type": "tool",
    "is_reviewable": true,
    "confidence": 0.92,
    "domain": "database",
    "app_type": "database-relational",
    "description": "Distributed SQLite-compatible database with edge replication",
    "use_modes": ["CLI", "HTTP API", "SDK"],
    "similar_tools": ["PlanetScale", "Neon", "SQLite", "DuckDB"],
    "proposed_tests": [
      "Install libsql CLI and create a database",
      "Insert 1000 rows and measure write latency",
      "Run a SELECT with WHERE clause, measure query latency",
      "Compare latency vs SQLite in-process"
    ],
    "requires_api_key": false,
    "is_open_source": true,
    "repo_url": "https://github.com/tursodatabase/libsql"
  }
]
```

## Field definitions

- **is_reviewable**: true if this is a concrete tool/project a developer can use or evaluate
- **domain**: broad category (see Domain taxonomy below)
- **app_type**: specific type within domain (see App type taxonomy below)
- **source_type**: `"tool"` | `"article"` | `"tutorial"` | `"research"` | `"dataset"` | `"model"`
- **tool_url**: the actual tool/repo URL (not the article URL)
- **repo_url**: GitHub/GitLab URL if known

## What to include (is_reviewable = true)

**The primary criterion**: there must be a concrete, installable or runnable software
artifact that can be tested independently. Ask: "Can I download/install/run this right now?"

- **Show HN** posts with a tool, library, framework, app, or open-source project
- Research papers that ship a named, runnable artifact (code, model, dataset)
- Open datasets or benchmarks with a download URL
- Open-source models people can run locally

## What to exclude (is_reviewable = false)

- Blog posts and personal stories ("Eight years of wanting...", "How I built X")
- Tutorials that explain how to use an *existing* tool — no new software introduced
- Articles about tools that already exist (e.g. "Running Gemma with LM Studio" → LM Studio is not new)
- Opinion pieces, editorials, news about companies or funding
- Ask HN / Tell HN with no linked software artifact
- Paywalled content with no evaluable artifact
- Videos, podcasts, or slide decks without accompanying code
- Announcements of features in closed/proprietary SaaS with no testable interface

**Key rule**: if the item's primary value is the *writing* rather than the *software*, exclude it.
A blog post that mentions 10 tools is NOT 10 reviewable items — it is 0.

## Article / post handling (narrow exception)

Include an article ONLY if ALL of the following are true:
1. The article introduces a **new, specific tool** not previously known
2. That tool has its own GitHub/package URL distinct from the article URL
3. The tool can be installed and tested independently of the article

Examples:
- OK: "Show HN: I built FastEval" → tool_url = github.com/x/fasteval (new tool, runnable)
- OK: Article with inline code + GitHub repo → tool_url = the repo, tests run against the code
- NOT OK: "Running Gemma 4 with LM Studio" → LM Studio already exists, no new tool
- NOT OK: "Eight years of wanting, built with AI" → personal story, no software artifact
- NOT OK: "How we use LangChain in production" → tutorial about existing tool, no new code

**What gets tested is always the code, never the article itself.**
If an article links to a repo with runnable code → include it, set tool_url to the repo, run tests on that code.
If an article has inline code snippets but no repo → exclude (not independently installable).
If an article describes a technique with no named tool → exclude.

---

## Domain taxonomy

```
llm-ai       | devtool     | database    | infrastructure
language     | security    | data        | web
mobile       | hardware    | research    | other
```

## App type taxonomy (by domain)

### llm-ai
```
llm-framework       – agent frameworks, orchestrators (LangChain, CrewAI)
llm-evaluation      – benchmarking, evals, scoring LLMs (lm-eval-harness)
llm-inference       – model servers, inference optimization (Ollama, vLLM)
llm-training        – fine-tuning, RLHF, alignment (Axolotl, Unsloth)
rag-system          – retrieval-augmented generation pipelines
vector-db           – vector databases marketed for LLMs (Chroma, Weaviate)
prompt-tool         – prompt management, templating, DSPy
llm-assistant       – coding assistants, chat UIs, copilots
multimodal          – image/audio/video AI tools
```

### devtool
```
devtool-editor      – editors, IDEs, plugins, extensions
devtool-testing     – testing frameworks, QA, mocking
devtool-build       – build systems, bundlers, compilers (Vite, Turbopack)
devtool-cicd        – CI/CD, deployment, release tools
devtool-debug       – debuggers, profilers, APM
devtool-cli         – CLI utilities, shell tools, TUI apps
devtool-codegen     – scaffolding, code generation, boilerplate
devtool-linter      – linters, formatters, static analysis
devtool-monitoring  – observability, logging, metrics, tracing
```

### database
```
database-relational – SQL databases and extensions (PostgreSQL forks, SQLite variants)
database-nosql      – document, key-value, wide-column stores
database-timeseries – time-series databases (InfluxDB alternatives)
database-graph      – graph databases (Neo4j alternatives)
database-search     – search engines (Meilisearch, Typesense)
database-olap       – analytical/OLAP engines (DuckDB, ClickHouse)
database-cache      – caching layers (Redis alternatives, Dragonfly)
database-orm        – ORMs, query builders, schema tools
```

### infrastructure
```
infra-container     – container orchestration, k8s tooling
infra-networking    – proxies, load balancers, service mesh, VPN
infra-storage       – object storage, file systems, blob stores
infra-queue         – message queues, pub/sub, event streaming
infra-iac           – infrastructure-as-code, configuration management
infra-cloud         – cloud tooling, multi-cloud, cost optimization
infra-api-gateway   – API gateways, reverse proxies
```

### language
```
lang-new            – new programming languages
lang-runtime        – runtimes, VMs, WebAssembly
lang-type-system    – type checkers, gradual typing
lang-transpiler     – transpilers, source-to-source compilers
lang-package-manager – package managers, dependency tools
```

### security
```
sec-scanner         – vulnerability scanners, SAST, DAST
sec-auth            – authentication, authorization, SSO
sec-crypto          – cryptography libraries, key management
sec-network         – network security, firewalls, intrusion detection
sec-secrets         – secrets management, vaults
```

### data
```
data-pipeline       – ETL, ELT, streaming pipelines
data-viz            – charts, dashboards, BI tools
data-format         – serialization formats, codecs, schema tools
data-analytics      – query engines, notebooks, exploration
data-scraping       – web scrapers, crawlers, extractors
```

### web
```
web-framework       – backend frameworks, API libraries
web-frontend        – frontend frameworks, UI component libraries
web-cms             – content management, headless CMS
web-ecommerce       – commerce platforms, payment tools
web-extension       – browser extensions, userscripts
web-saas            – full SaaS apps with public API
```

### mobile / hardware / research
```
mobile-cross        – cross-platform mobile frameworks
mobile-native       – iOS/Android native tools
hardware-iot        – IoT firmware, sensor tools, embedded
hardware-robotics   – robotics, simulation, control
research-paper      – academic paper with runnable code
research-dataset    – open datasets, curated benchmarks
research-model      – open-source ML models
```

---

## QA test proposal logic (by app_type)

Propose 3–5 concrete, automatable tests based on app_type:

| Domain/type           | Test focus                                                      |
|-----------------------|-----------------------------------------------------------------|
| llm-*                 | pip install, import, mock API call, latency benchmark           |
| devtool-cli           | install, --help, basic command, measure execution time          |
| devtool-testing       | install, write 1 test, run test suite, check output format      |
| devtool-build         | install, build a hello-world project, measure build time        |
| database-*            | install, create schema, insert rows, query, measure latency     |
| database-search       | install, index docs, query, measure relevance + latency         |
| infra-container       | docker pull, run hello-world, check health endpoint             |
| infra-queue           | install, produce 100 messages, consume, measure throughput      |
| lang-new              | download, compile hello-world, measure compile+run time         |
| lang-runtime          | install, run benchmark script, compare vs baseline runtime      |
| sec-scanner           | install, scan a sample repo, count findings, compare vs semgrep |
| sec-auth              | install, configure, test token issuance + validation            |
| data-pipeline         | install, run pipeline on synthetic data, measure throughput     |
| data-viz              | install, generate chart from CSV, check output format           |
| web-framework         | install, scaffold hello-world, benchmark requests/sec           |
| research-paper        | clone repo, run provided example, verify output matches paper   |
| hardware-*            | check simulator/emulator, run example, check docs               |

---

## Community adaptation notes
- Add new `app_type` values as the ecosystem evolves
- Adjust inclusion/exclusion rules for specific communities
- `domain` is the primary grouping lever for newsletters and weekly top-5 diversity
