# SKILL: app-benchmarker

## Purpose
Generate and execute **type-specific benchmark suites** for ANY app published on
Hacker News — not just LLM tools. HN publishes databases, devtools, programming
languages, security tools, web frameworks, and more. This skill adapts benchmarks,
baselines, and score formulas to each `app_type`.

Produces quantitative metrics that feed directly — via explicit formulas — into
the scorer's 10 criteria. Three criteria are **calculated deterministically**;
the rest use metrics as mandatory citations for LLM judgment.

## Trigger
Called between `app-identifier` and `app-scorer`. Replaces the generic
`generateTestScript()` in `container-runner.js`.

## Design principles

1. **Quantitative linkage is mandatory**: every metric maps to at least one scoring
   criterion via a published formula. No metric without a formula. No score without a metric.
2. **Baselines are type-specific**: "200ms is fast" depends on the category. Each app
   type declares its own reference values.
3. **Three scores are calculated, not judged**: `system_requirements`, `ease_of_use`,
   `performance`. The remaining seven use metrics as citations for LLM judgment.
4. **HN context**: HN showcases early-stage projects. Rubrics weight *promise + direction*
   over *production completeness*. A v0.1 with clear original contribution outranks a polished clone.
5. **Article/tutorial distinction**: when `source_type ≠ "tool"`, benchmarks run against
   `tool_url`, not the article URL. `ease_of_use` reflects the tool, not the post.

---

## Input
```json
{
  "app": {
    "title": "Turso",
    "tool_url": "https://github.com/tursodatabase/libsql",
    "source_type": "tool",
    "domain": "database",
    "app_type": "database-relational",
    "use_modes": ["CLI", "HTTP API", "SDK"],
    "is_open_source": true,
    "requires_api_key": false,
    "similar_tools": ["PlanetScale", "SQLite", "Neon"]
  }
}
```

## Output
```json
{
  "run_id": "bench-20250115-abc12",
  "domain": "database",
  "app_type": "database-relational",
  "benchmark_version": "1.1",
  "metrics": {
    "install_time_s":      8.2,
    "install_success":     true,
    "import_time_ms":      95,
    "basic_run_success":   true,
    "tests_passed":        4,
    "tests_total":         5,
    "core_latency_ms":     12,
    "baseline_latency_ms": 18,
    "memory_mb":           45,
    "baseline_memory_mb":  60,
    "throughput_rps":      8400,
    "setup_steps":         2,
    "api_modes_count":     3,
    "has_streaming":       false,
    "type_specific": {}
  },
  "calculated_scores": {
    "system_requirements": 9,
    "ease_of_use":         8,
    "performance":         8
  },
  "benchmark_log": "INSTALL_OK\nTEST_PASS:create_db\n...",
  "error_log": ""
}
```

---

## Score formulas (deterministic — applied by scorer directly)

### system_requirements
```
Base = install_success ? 6 : 1

if install_success:
  if install_time_s < 15:   Base += 3   → 9
  elif install_time_s < 30: Base += 2   → 8
  elif install_time_s < 60: Base += 1   → 7
  elif install_time_s < 120: Base += 0  → 6
  else:                      Base -= 1  → 5

  if requires_api_key:     Base -= 1
  if has_pypi_or_npm:      Base += 1  (cap 10)
  if needs_docker_only:    Base -= 1  (extra friction)

S_req = clamp(Base, 1, 10)
```

### ease_of_use
```
pass_rate = tests_passed / tests_total  (0 if tests_total == 0)

if !install_success:       E_use = 2
elif pass_rate == 1.0:     E_use = 9
elif pass_rate >= 0.8:     E_use = 7
elif pass_rate >= 0.6:     E_use = 6
elif pass_rate >= 0.4:     E_use = 4
elif pass_rate > 0:        E_use = 3
else:                      E_use = 2

Bonus:   +1 if basic_run_success AND error_log is empty   (cap 10)
Penalty: -1 if error_log contains "DeprecationWarning" or "breaking change"
```

### performance
```
if core_latency_ms is null:
  P_perf = 5  # Neutral — no benchmark data

else:
  ratio = core_latency_ms / baseline_latency_ms
  P_perf:
    ratio < 0.50 → 10   # >2× faster than baseline
    ratio < 0.70 → 9
    ratio < 0.85 → 8
    ratio < 1.00 → 7
    ratio < 1.20 → 6    # Comparable
    ratio < 1.50 → 5
    ratio < 2.00 → 4
    ratio < 3.00 → 3
    else         → 2

  # Throughput bonus
  if throughput_rps is not null and baseline_throughput_rps is not null:
    t_ratio = throughput_rps / baseline_throughput_rps
    if t_ratio > 2.0:  P_perf = min(10, P_perf + 1)
    elif t_ratio < 0.5: P_perf = max(1, P_perf - 1)

  # Memory modifier
  if memory_mb and baseline_memory_mb:
    mem_ratio = memory_mb / baseline_memory_mb
    if mem_ratio < 0.5:   P_perf = min(10, P_perf + 1)
    elif mem_ratio > 2.0: P_perf = max(1,  P_perf - 1)
```

---

## Criterion → metric mapping (contract with app-scorer)

| Scoring criterion      | Calculated from                        | Cited by LLM scorer                      |
|------------------------|----------------------------------------|------------------------------------------|
| system_requirements    | install_time_s, install_success        | requires_api_key, use_modes, has_pypi    |
| ease_of_use            | tests_passed/total, basic_run_success  | error_log quality, has_streaming         |
| performance            | core_latency_ms/baseline, memory_mb    | throughput_rps, type_specific.*          |
| novelty                | *(LLM judgment)*                       | days_since_created, is_fork, similar_tools |
| current_relevance      | *(LLM judgment)*                       | domain, app_type, ecosystem trends       |
| differentiation        | *(LLM judgment)*                       | core_latency vs similar, stars comparison |
| community              | *(LLM judgment)*                       | github.stars, contributors, days_since_update |
| ease_of_integration    | api_modes_count, has_pypi_or_npm       | use_modes, license                       |
| documentation          | *(LLM judgment)*                       | has_wiki, has_pages, README quality      |
| maturity               | *(LLM judgment)*                       | version, days_since_created, forks       |

**Rule**: never score a criterion without citing at least one metric from its row.
Null metric → score 5, state reason explicitly.

---

## Type-specific benchmark suites

### LLM/AI DOMAIN

#### llm-framework / llm-assistant
**Baseline**: LangChain (install ~30s, import ~1200ms, simple chain ~500ms, ~300MB RAM)
```
1. pip install → install_time_s, install_success
2. import timing → import_time_ms
3. Create minimal agent with stub LLM → TEST_PASS:agent_creation, core_latency_ms
4. Check streaming support → has_streaming
5. Count supported LLM backends → type_specific.backends_count
6. Memory footprint (tracemalloc) → memory_mb
   BENCHMARK:baseline_latency_ms:500, BENCHMARK:baseline_memory_mb:300
```

#### llm-evaluation / llm-inference
**Baseline**: lm-eval-harness (install ~45s, import ~800ms, 1 task ~2000ms, ~400MB)
```
1. pip install → install_time_s, install_success
2. import timing → import_time_ms
3. Run --help, list metrics → TEST_PASS:cli_help, type_specific.metrics_count
4. Run smallest eval task (mock data) → core_latency_ms, TEST_PASS:basic_eval
5. Custom metric plugin test → type_specific.custom_metric_ok
   BENCHMARK:baseline_latency_ms:2000, BENCHMARK:baseline_memory_mb:400
```

#### rag-system / vector-db
**Baseline**: ChromaDB in-process (index 10 docs ~200ms, query ~50ms, ~150MB)
```
1. pip install → install_time_s, install_success
2. Create in-memory collection → import_time_ms, TEST_PASS:create_collection
3. Index 10 synthetic documents → type_specific.index_latency_ms, TEST_PASS:indexing
4. Run 5 semantic queries (avg) → core_latency_ms, TEST_PASS:query
5. Verify relevance (keyword match in top result) → TEST_PASS/FAIL:relevance
6. Count setup steps from README → setup_steps
   BENCHMARK:baseline_latency_ms:50, BENCHMARK:baseline_memory_mb:150
```

#### llm-training / prompt-tool
**Baseline**: HuggingFace PEFT (install ~40s, import ~600ms)
```
1. pip install → install_time_s, install_success
2. import timing → import_time_ms
3. Load smallest config / create prompt template → TEST_PASS:basic_setup
4. Run with mock data (no GPU required) → core_latency_ms, TEST_PASS:mock_run
5. API surface count (public methods) → api_modes_count
   BENCHMARK:baseline_latency_ms:600, BENCHMARK:baseline_memory_mb:500
```

---

### DEVTOOL DOMAIN

#### devtool-cli / devtool-linter / devtool-debug
**Baseline**: ripgrep (install ~5s, --help ~10ms, scan 1000 files ~200ms)
```
1. Install via pip/npm/cargo/brew → install_time_s, install_success
2. Run --help or --version → TEST_PASS:cli_help, import_time_ms (first exec)
3. Run on a synthetic 50-file project → core_latency_ms, TEST_PASS:basic_run
4. Count available subcommands/flags → api_modes_count
5. Compare output format (JSON/structured?) → type_specific.has_structured_output
   BENCHMARK:baseline_latency_ms:200, BENCHMARK:baseline_memory_mb:30
```

#### devtool-testing
**Baseline**: pytest (install ~10s, collect 10 tests ~300ms, run ~500ms)
```
1. pip/npm install → install_time_s, install_success
2. Write 3 synthetic tests, run suite → core_latency_ms, TEST_PASS:run_suite
3. Check output formats (JUnit XML, TAP) → type_specific.output_formats
4. Test watch mode existence → type_specific.has_watch_mode
5. Measure test discovery speed → type_specific.discovery_ms
   BENCHMARK:baseline_latency_ms:500, BENCHMARK:baseline_memory_mb:50
```

#### devtool-build
**Baseline**: esbuild (install ~5s, build hello-world ~50ms, ~20MB RAM)
```
1. Install → install_time_s, install_success
2. Build a synthetic hello-world JS/TS project → core_latency_ms, TEST_PASS:build_ok
3. Build 100-file synthetic project → type_specific.large_build_ms
4. Measure output bundle size → type_specific.bundle_size_kb
5. Check incremental build support → type_specific.has_incremental
   BENCHMARK:baseline_latency_ms:50, BENCHMARK:baseline_memory_mb:20
```

#### devtool-monitoring / devtool-cicd
**Baseline**: Prometheus (install ~10s, scrape ~100ms, ~200MB)
```
1. Install / docker pull → install_time_s, install_success
2. Start with minimal config → TEST_PASS:startup, core_latency_ms (first scrape/run)
3. Check API/UI availability → TEST_PASS:api_health
4. Ingest synthetic metrics/events → throughput_rps
5. Count integrations (exporters, plugins) → type_specific.integrations_count
   BENCHMARK:baseline_latency_ms:100, BENCHMARK:baseline_memory_mb:200
```

---

### DATABASE DOMAIN

#### database-relational / database-nosql
**Baseline**: SQLite in-process (1000 inserts ~20ms, SELECT ~5ms, ~10MB)
```
1. Install client lib → install_time_s, install_success
2. Create in-memory DB, run schema → import_time_ms, TEST_PASS:create_schema
3. Insert 1000 rows → type_specific.write_latency_ms, TEST_PASS:bulk_insert
4. SELECT with WHERE (indexed) → core_latency_ms, TEST_PASS:query
5. Measure concurrent reads (5 threads) → throughput_rps
6. Count supported query features → type_specific.features_count
   BENCHMARK:baseline_latency_ms:5, BENCHMARK:baseline_memory_mb:10
```

#### database-search
**Baseline**: Meilisearch (index 1000 docs ~500ms, query ~10ms, ~150MB)
```
1. Install / docker pull → install_time_s, install_success
2. Index 1000 synthetic documents → type_specific.index_latency_ms, TEST_PASS:indexing
3. Run 10 search queries → core_latency_ms (avg), TEST_PASS:search
4. Check typo-tolerance, faceting, filters → type_specific.features_count
5. Relevance check (top result matches query keyword) → TEST_PASS/FAIL:relevance
   BENCHMARK:baseline_latency_ms:10, BENCHMARK:baseline_memory_mb:150
```

#### database-olap
**Baseline**: DuckDB (install ~5s, query 1M rows ~80ms, ~50MB)
```
1. pip/npm install → install_time_s, install_success
2. Load 1M-row synthetic Parquet → type_specific.load_latency_ms, TEST_PASS:load
3. Aggregation query (GROUP BY, SUM) → core_latency_ms, TEST_PASS:aggregation
4. Join two 100k-row tables → type_specific.join_latency_ms, TEST_PASS:join
5. Measure peak memory during query → memory_mb
   BENCHMARK:baseline_latency_ms:80, BENCHMARK:baseline_memory_mb:50
```

#### database-cache
**Baseline**: Redis (install ~5s, SET/GET ~1ms, ~10MB, ~100k ops/s)
```
1. Install / docker pull → install_time_s, install_success
2. SET 1000 keys, GET 1000 keys → core_latency_ms (avg), TEST_PASS:get_set
3. Measure throughput (ops/sec) → throughput_rps
4. Test TTL expiration → TEST_PASS:ttl
5. Check data structure support (hash, list, sorted set) → type_specific.structures_count
   BENCHMARK:baseline_latency_ms:1, BENCHMARK:baseline_throughput_rps:100000
```

#### database-orm
**Baseline**: SQLAlchemy (install ~15s, define model ~50ms, query ~10ms)
```
1. pip/npm install → install_time_s, install_success
2. Define 3-model schema → import_time_ms, TEST_PASS:define_schema
3. Insert + query with relations → core_latency_ms, TEST_PASS:crud
4. Check migration tool existence → type_specific.has_migrations
5. Count supported databases → type_specific.backends_count
   BENCHMARK:baseline_latency_ms:10, BENCHMARK:baseline_memory_mb:40
```

---

### INFRASTRUCTURE DOMAIN

#### infra-queue / infra-networking
**Baseline**: RabbitMQ (install ~30s, publish 1k msgs ~200ms, ~100MB)
```
1. docker pull / install → install_time_s, install_success
2. Start broker, connect producer+consumer → TEST_PASS:connect
3. Publish 1000 messages, consume all → core_latency_ms, throughput_rps
4. Test persistence / durability → TEST_PASS/FAIL:durability
5. Count protocol support (AMQP, MQTT, STOMP) → type_specific.protocols_count
   BENCHMARK:baseline_latency_ms:200, BENCHMARK:baseline_throughput_rps:5000
```

#### infra-container
**Baseline**: kubectl (install ~10s, pod start ~2000ms, health check ~50ms)
```
1. Install CLI → install_time_s, install_success
2. Run --help, check subcommands → TEST_PASS:cli_help, api_modes_count
3. Deploy minimal pod/container (minikube or mock) → core_latency_ms, TEST_PASS:deploy
4. Health check endpoint → TEST_PASS:health
5. Count CRD/plugins supported → type_specific.extensions_count
   BENCHMARK:baseline_latency_ms:2000, BENCHMARK:baseline_memory_mb:100
```

---

### LANGUAGE DOMAIN

#### lang-new / lang-runtime
**Baseline**: Python 3 (install ~0s if present, hello-world ~50ms, fib(30) ~200ms)
```
1. Download + install → install_time_s, install_success
2. Compile + run hello-world → core_latency_ms, TEST_PASS:hello_world
3. Run fibonacci(35) → type_specific.fib35_ms (compute benchmark)
4. Run string processing (1M chars) → type_specific.string_ms
5. Compare vs baseline (Python) → BENCHMARK:vs_python_fib:<ratio>
6. Check package manager existence → type_specific.has_package_manager
   BENCHMARK:baseline_latency_ms:200
```

#### lang-transpiler / lang-package-manager
**Baseline**: npm (install ~5s, resolve 10 deps ~2000ms)
```
1. Install tool → install_time_s, install_success
2. Transpile/resolve synthetic project → core_latency_ms, TEST_PASS:basic_run
3. Handle 50-dependency project → type_specific.large_resolve_ms
4. Check lockfile generation → type_specific.has_lockfile
5. Measure disk usage → type_specific.disk_mb
   BENCHMARK:baseline_latency_ms:2000
```

---

### SECURITY DOMAIN

#### sec-scanner / sec-auth
**Baseline**: Semgrep (install ~20s, scan 100 files ~5000ms, ~200MB)
```
1. pip/npm install → install_time_s, install_success
2. Scan a 50-file synthetic project → core_latency_ms, TEST_PASS:scan_run
3. Count finding categories → type_specific.rule_categories
4. Check CI integration (GitHub Actions / JSON output) → type_specific.has_ci_export
5. False-positive check on clean code → TEST_PASS/FAIL:false_positive_rate
   BENCHMARK:baseline_latency_ms:5000, BENCHMARK:baseline_memory_mb:200
```

---

### DATA DOMAIN

#### data-pipeline
**Baseline**: Prefect (install ~30s, DAG run 3 tasks ~500ms)
```
1. pip install → install_time_s, install_success
2. Define 3-step pipeline on synthetic data → TEST_PASS:pipeline_create
3. Run pipeline → core_latency_ms, throughput_rps
4. Test retry on failure → TEST_PASS:error_handling
5. Check observability (logs, metrics) → type_specific.has_observability
   BENCHMARK:baseline_latency_ms:500, BENCHMARK:baseline_memory_mb:250
```

#### data-viz
**Baseline**: Matplotlib (install ~10s, render chart ~300ms, ~80MB)
```
1. pip/npm install → install_time_s, install_success
2. Generate bar chart from synthetic CSV → core_latency_ms, TEST_PASS:basic_chart
3. Render interactive chart (if claimed) → TEST_PASS/SKIP:interactive
4. Export to PNG/SVG → TEST_PASS:export
5. Count chart types supported → type_specific.chart_types
   BENCHMARK:baseline_latency_ms:300, BENCHMARK:baseline_memory_mb:80
```

#### data-analytics / data-scraping
**Baseline**: Pandas (install ~15s, process 100k rows ~500ms, ~200MB)
```
1. pip install → install_time_s, install_success
2. Load + process 100k-row synthetic dataset → core_latency_ms, TEST_PASS:process
3. Filter + aggregate → type_specific.query_ms
4. Export result (CSV/Parquet) → TEST_PASS:export
5. Check streaming support for large files → type_specific.has_streaming
   BENCHMARK:baseline_latency_ms:500, BENCHMARK:baseline_memory_mb:200
```

---

### WEB DOMAIN

#### web-framework / web-frontend
**Baseline**: Express.js (install ~10s, hello-world ~50ms startup, ~1000 req/s)
```
1. npm/pip install → install_time_s, install_success
2. Scaffold hello-world app → TEST_PASS:scaffold
3. Start server, measure startup → core_latency_ms (startup), TEST_PASS:start
4. Benchmark: 1000 GET requests → throughput_rps
5. Check middleware/plugin ecosystem → type_specific.plugins_count
   BENCHMARK:baseline_latency_ms:50, BENCHMARK:baseline_throughput_rps:1000
```

#### web-extension / web-saas
**Baseline**: N/A (check existence, install, basic function test)
```
1. Install via npm/pip or check manifest → install_time_s, install_success
2. Load extension/start service → core_latency_ms, TEST_PASS:start
3. Call primary API endpoint → TEST_PASS:api_call
4. Check rate limits / free tier → type_specific.has_free_tier
5. Count API endpoints → api_modes_count
   BENCHMARK:baseline_latency_ms:500
```

---

### RESEARCH DOMAIN

#### research-paper / research-model
**Baseline**: varies — compare against paper's own reported numbers
```
1. Clone repo + pip install → install_time_s, install_success
2. Run provided example script → TEST_PASS:example_runs, core_latency_ms
3. Verify output matches paper's reported result (within 10%) → TEST_PASS/FAIL:reproducibility
4. Check model size / memory requirement → memory_mb
5. Count tasks/datasets supported → type_specific.tasks_count
   BENCHMARK:baseline_latency_ms: use paper's reported value
   BENCHMARK:reproducibility_delta:<% difference from paper>
```

---

## HN-context scoring adjustments

| App state                                        | Adjustment                                              |
|--------------------------------------------------|---------------------------------------------------------|
| `days_since_created` < 30                        | novelty_floor = 6 (new projects get benefit of doubt)   |
| `is_fork == true`                                | novelty_cap = 6 (forks need explicit new contribution)  |
| `source_type == "article"`                       | ease_of_use scored on tool, not article                 |
| `requires_api_key == true`                       | system_requirements capped at 7                         |
| `tests_total == 0` (untestable)                  | ease_of_use = 3, performance = 5, noted in log          |
| `domain == "research"` and stars < 100           | community_floor = 4 (academic projects are niche)       |
| `domain == "hardware"` (no pip/npm)              | system_requirements formula skips install_time penalty  |
| GitHub stars < 50 AND days_since_created < 14   | community_floor = 4 (too new to judge)                  |

---

## weekly-top5 weights by domain

Replace static weight table with domain-aware weights:

```
Default:
  novelty: 1.4, current_relevance: 1.3, differentiation: 1.3,
  performance: 1.1, ease_of_use: 1.0, ease_of_integration: 1.0,
  community: 0.8, system_requirements: 0.7, documentation: 0.6, maturity: 0.6

Domain overrides (applied on top of default):
  llm-ai:        novelty×1.6, performance×1.3, ease_of_integration×1.2
  database:      performance×1.6, ease_of_integration×1.4, system_requirements×1.2
  devtool:       ease_of_use×1.4, ease_of_integration×1.3, performance×1.2
  language:      novelty×1.7, performance×1.5, community×0.9
  security:      ease_of_use×1.3, documentation×1.3, maturity×1.2
  infrastructure: ease_of_integration×1.5, system_requirements×1.3, maturity×1.2
  data:          performance×1.3, ease_of_integration×1.2
  web:           ease_of_use×1.3, ease_of_integration×1.2, community×1.1
  research:      novelty×1.8, performance×1.4, community×0.6
  hardware:      novelty×1.5, documentation×1.3, community×0.7
```

---

## Output markers (emitted by test script)

```
INSTALL_OK | INSTALL_FAIL:<reason>
RUN_OK
TEST_PASS:<name>
TEST_FAIL:<name>:<reason>
TEST_SKIP:<name>:<reason>
BENCHMARK:install_time_s:<value>
BENCHMARK:import_time_ms:<value>
BENCHMARK:core_latency_ms:<value>
BENCHMARK:baseline_latency_ms:<value>
BENCHMARK:memory_mb:<value>
BENCHMARK:baseline_memory_mb:<value>
BENCHMARK:throughput_rps:<value>
BENCHMARK:baseline_throughput_rps:<value>
BENCHMARK:setup_steps:<value>
BENCHMARK:api_modes_count:<value>
BENCHMARK:has_streaming:<true|false>
BENCHMARK:type:<key>:<value>
```

---

## Incoherence fixes applied

| # | Issue | Fix |
|---|-------|-----|
| 1 | Scope limited to LLM apps | Covers all HN app domains |
| 2 | system_requirements and ease_of_use shared install_success | Split: S_req = install access, E_use = runtime UX |
| 3 | community and maturity overlapped on GitHub data | community = social signal, maturity = lifecycle stage |
| 4 | performance had no type-specific baselines | Per-type baselines declared in every suite |
| 5 | Scores were LLM-interpreted, not computed | 3 criteria now have deterministic formulas |
| 6 | weekly-top5 ignored performance in weights | performance weight = 1.1 default + domain overrides |
| 7 | Articles: ease_of_use was ambiguous | Explicit rule: score the tool, cite source_type |
| 8 | data-pipeline had no test strategy | Added full suite |
| 9 | Newsletter bar showed 0–70 for 0–100 scale | Bug noted: fix bar width = score% of 100 |
| 10 | No domain-aware weekly weights | Full domain weight table added |

---

## Community adaptation notes

- To add a new domain: define baselines, test steps, type_specific metrics, and weight overrides.
- To adjust for a specific community: override domain weights.
- Performance formula is versioned (`benchmark_version`) so historical scores stay comparable.
