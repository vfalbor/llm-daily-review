# SKILL: app-identifier

## Purpose
Given a list of HN items, identify which ones are applications or systems related
to LLMs, AI agents, or generative AI. For each match, classify the app type,
identify similar tools, and propose QA benchmarks.

## Trigger
Called by orchestrator after hn-scraper, receives raw item list.

## Input
```json
[
  { "title": "...", "url": "...", "rank": 1, ... }
]
```

## Output
```json
[
  {
    "title": "FastEval",
    "url": "https://...",
    "is_llm_related": true,
    "confidence": 0.95,
    "app_type": "benchmark-runner",
    "description": "Open-source LLM evaluation framework with pluggable metrics",
    "use_modes": ["CLI", "Python API", "self-hosted"],
    "similar_tools": ["lm-evaluation-harness", "Evals by OpenAI", "HELM"],
    "proposed_tests": [
      "Install and run on a small model (phi-2 or similar)",
      "Measure time-to-first-result",
      "Test custom metric plugin",
      "Check documentation completeness"
    ],
    "requires_api_key": false,
    "is_open_source": true,
    "repo_url": "https://github.com/..."
  }
]
```

## Classification rules

### Include (is_llm_related = true)
- LLM wrappers, SDKs, frameworks
- Prompt engineering tools
- RAG systems and vector DBs marketed for LLMs
- Agent frameworks and orchestrators
- LLM evaluation and benchmarking tools
- Fine-tuning utilities
- LLM-powered apps with accessible API/SDK
- Model serving infrastructure

### Exclude (is_llm_related = false)
- General-purpose software that mentions AI in passing
- Pure research papers without runnable code
- News articles, blog posts, opinion pieces
- Closed-source SaaS with no testable interface

## App type taxonomy
```
benchmark-runner | agent-framework | rag-system | prompt-tool |
fine-tuning | model-server | sdk-wrapper | evaluation | 
vector-db | multimodal | code-assistant | data-pipeline | other-llm
```

## QA test proposal logic
Based on `app_type`, propose 3–5 concrete, automatable tests:
- If CLI tool → test installation and basic command
- If Python package → test `pip install` + import + minimal example
- If web app → test signup flow, first API call, response quality
- If Docker image → test `docker pull` + `docker run` + health check

## Community adaptation notes
This skill is designed to be extended:
- Add new `app_type` values as the ecosystem evolves
- Adjust inclusion/exclusion rules for different communities
- Add domain-specific classifiers (e.g., bio-LLM, legal-AI)
