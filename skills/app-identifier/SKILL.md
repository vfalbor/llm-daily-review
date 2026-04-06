# SKILL: app-identifier

## Purpose
Given a list of HN items, identify which ones are related to LLMs, AI agents, or
generative AI — whether they are the tool itself **or an article/post that describes a
specific tool**. For each match, extract the actual tool URL, classify the type, identify
similar tools, and propose QA benchmarks.

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
    "rank": 1,
    "title": "FastEval",
    "url": "https://...",
    "tool_url": "https://github.com/fasteval/fasteval",
    "source_type": "tool",
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
    "repo_url": "https://github.com/fasteval/fasteval"
  }
]
```

## Field definitions

- **url**: original HN post URL (keep as-is)
- **tool_url**: the actual tool/library/repo URL to test and score. For direct tool posts
  this equals `url`. For articles, extract the tool's GitHub repo or website URL from
  the title/context. If the tool URL cannot be determined, set to `null`.
- **source_type**: `"tool"` (direct link to the tool) | `"article"` (blog post / write-up
  about a tool) | `"tutorial"` (how-to guide using a specific tool)
- **repo_url**: GitHub repo URL if known (same as tool_url when it's a GitHub link)

## Article / post handling — IMPORTANT

**Articles and tutorials that describe a specific LLM tool ARE included** (`is_llm_related: true`).
For these, you MUST:
1. Set `source_type` to `"article"` or `"tutorial"`
2. Infer the actual tool's GitHub/package URL from the title and context, set it as `tool_url`
3. Set `app_type`, `similar_tools`, `proposed_tests` for the described tool — not the article
4. Example: "Eight years wanting, built with LangGraph" → tool_url = "https://github.com/langchain-ai/langgraph"
5. Example: "How we reduced LLM costs with Outlines" → tool_url = "https://github.com/outlines-dev/outlines"
6. If the article is about a generic technique with no specific tool, set `is_llm_related: false`

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
- **Articles and tutorials about any of the above** (set source_type accordingly)

### Exclude (is_llm_related = false)
- General-purpose software that mentions AI in passing
- Pure research papers without a named, runnable tool
- Opinion pieces about AI with no specific tool
- Closed-source SaaS with no testable interface and no article about a specific tool

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
- For articles: propose tests for the actual tool described, not the article URL

## Community adaptation notes
This skill is designed to be extended:
- Add new `app_type` values as the ecosystem evolves
- Adjust inclusion/exclusion rules for different communities
- Add domain-specific classifiers (e.g., bio-LLM, legal-AI)
