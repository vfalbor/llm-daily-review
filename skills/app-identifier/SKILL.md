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

- **Show HN** posts with a concrete tool, library, app, or project
- Articles/tutorials that describe a specific named tool (set source_type accordingly)
- Research papers with runnable code or a named artifact
- Open datasets or benchmarks people can use
- Open-source models people can run locally

## What to exclude (is_reviewable = false)

- Pure opinion pieces ("AI will change everything")
- Ask HN questions with no specific tool
- News about companies (funding, acquisitions) with no new tool
- Generic tutorials with no specific tool (e.g., "How to learn Python")
- Paywalled content with no evaluable artifact

## Article / post handling

For articles that describe a specific tool:
1. Set `source_type = "article"` or `"tutorial"`
2. Infer `tool_url` from title/context (e.g. "How we built X with Drizzle ORM" → drizzle-orm GitHub)
3. Set `app_type` for the described tool, not the article
4. Proposed tests target the tool, not the article URL

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
