// src/enricher/data-enricher.js
// Fetches quantitative data for an app BEFORE scoring.
// Every score criterion gets concrete numbers, not guesses.

const GH_API = 'https://api.github.com';
const PYPI_API = 'https://pypi.org/pypi';
const NPM_API = 'https://registry.npmjs.org';

function ghHeaders() {
  return {
    'Accept': 'application/vnd.github+json',
    'Authorization': `Bearer ${process.env.GITHUB_TOKEN}`,
    'X-GitHub-Api-Version': '2022-11-28',
  };
}

// ── Main entry ───────────────────────────────────────────────────────────────

export async function enrichApp(app) {
  const data = {
    github: null,
    similar_github: [],
    pypi: null,
    npm: null,
  };

  // Prefer tool_url (set when HN post is an article about a specific tool)
  const resolvedUrl = app.tool_url || app.repo_url || app.url || '';
  const repoPath = extractGitHubRepo(resolvedUrl);

  if (repoPath) {
    data.github = await fetchGitHubRepo(repoPath);
    // Fetch stars for similar tools for comparison
    data.similar_github = await fetchSimilarToolsStats(app.similar_tools || []);
  }

  // PyPI lookup — use resolved URL for package name guessing
  const resolvedApp = { ...app, url: resolvedUrl };
  const pkgName = guessPyPIName(resolvedApp);
  if (pkgName) {
    data.pypi = await fetchPyPI(pkgName);
  }

  // npm lookup
  const npmName = guessNpmName(resolvedApp);
  if (npmName && !data.pypi) {
    data.npm = await fetchNpm(npmName);
  }

  return data;
}

// ── GitHub ───────────────────────────────────────────────────────────────────

function extractGitHubRepo(url) {
  const m = url.match(/github\.com\/([^/]+\/[^/?#]+)/i);
  if (!m) return null;
  return m[1].replace(/\.git$/, '');
}

async function fetchGitHubRepo(repoPath) {
  try {
    const [repoRes, contribRes] = await Promise.all([
      fetch(`${GH_API}/repos/${repoPath}`, { headers: ghHeaders() }),
      fetch(`${GH_API}/repos/${repoPath}/contributors?per_page=1&anon=true`, { headers: ghHeaders() }),
    ]);

    if (!repoRes.ok) return null;
    const repo = await repoRes.json();

    // GitHub returns contributor count in Link header when per_page=1
    let contributors = 0;
    if (contribRes.ok) {
      const link = contribRes.headers.get('link') || '';
      const lastPage = link.match(/page=(\d+)>; rel="last"/);
      contributors = lastPage ? parseInt(lastPage[1]) : 1;
    }

    const daysSinceUpdate = Math.floor(
      (Date.now() - new Date(repo.pushed_at)) / 86_400_000
    );
    const daysSinceCreated = Math.floor(
      (Date.now() - new Date(repo.created_at)) / 86_400_000
    );

    return {
      stars:             repo.stargazers_count,
      forks:             repo.forks_count,
      open_issues:       repo.open_issues_count,
      watchers:          repo.watchers_count,
      contributors,
      license:           repo.license?.spdx_id || 'none',
      language:          repo.language,
      is_fork:           repo.fork,
      days_since_update: daysSinceUpdate,
      days_since_created: daysSinceCreated,
      has_wiki:          repo.has_wiki,
      has_pages:         repo.has_pages,
      description:       repo.description,
      topics:            repo.topics || [],
    };
  } catch {
    return null;
  }
}

async function fetchSimilarToolsStats(similarTools) {
  const results = [];
  for (const tool of similarTools.slice(0, 3)) {
    // Try to guess GitHub repo from common tool names
    const knownRepos = {
      'langchain': 'langchain-ai/langchain',
      'llamaindex': 'run-llama/llama_index',
      'llama-index': 'run-llama/llama_index',
      'autogen': 'microsoft/autogen',
      'crewai': 'joaomdmoura/crewAI',
      'dspy': 'stanfordnlp/dspy',
      'haystack': 'deepset-ai/haystack',
      'semantic-kernel': 'microsoft/semantic-kernel',
      'guidance': 'guidance-ai/guidance',
      'outlines': 'outlines-dev/outlines',
      'lm-evaluation-harness': 'EleutherAI/lm-evaluation-harness',
      'helm': 'stanford-crfm/helm',
      'eleutherai evals': 'EleutherAI/lm-evaluation-harness',
      'openai evals': 'openai/evals',
      'ragas': 'explodinggradients/ragas',
      'deepeval': 'confident-ai/deepeval',
      'chromadb': 'chroma-core/chroma',
      'weaviate': 'weaviate/weaviate',
      'qdrant': 'qdrant/qdrant',
      'ollama': 'ollama/ollama',
      'vllm': 'vllm-project/vllm',
      'transformers': 'huggingface/transformers',
    };

    const key = tool.toLowerCase().replace(/\s+/g, '-');
    const repoPath = knownRepos[key] || knownRepos[tool.toLowerCase()];

    if (repoPath) {
      try {
        const res = await fetch(`${GH_API}/repos/${repoPath}`, { headers: ghHeaders() });
        if (res.ok) {
          const r = await res.json();
          results.push({ name: tool, stars: r.stargazers_count, repo: repoPath });
        }
      } catch { /* skip */ }
    } else {
      // Search GitHub for the tool
      try {
        const res = await fetch(
          `${GH_API}/search/repositories?q=${encodeURIComponent(tool)}+in:name&sort=stars&per_page=1`,
          { headers: ghHeaders() }
        );
        if (res.ok) {
          const data = await res.json();
          if (data.items?.length) {
            results.push({ name: tool, stars: data.items[0].stargazers_count, repo: data.items[0].full_name });
          }
        }
      } catch { /* skip */ }
    }
  }
  return results;
}

// ── PyPI ─────────────────────────────────────────────────────────────────────

function guessPyPIName(app) {
  // Try from title or repo name
  const candidates = [
    app.title?.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
    extractGitHubRepo(app.url || '')?.split('/')[1]?.toLowerCase(),
  ].filter(Boolean);

  return candidates[0] || null;
}

async function fetchPyPI(pkgName) {
  try {
    const res = await fetch(`${PYPI_API}/${pkgName}/json`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return null;
    const data = await res.json();
    const info = data.info;
    return {
      exists: true,
      version: info.version,
      summary: info.summary,
      requires_python: info.requires_python,
      license: info.license,
      home_page: info.home_page,
    };
  } catch {
    return null;
  }
}

// ── npm ──────────────────────────────────────────────────────────────────────

function guessNpmName(app) {
  if (!app.url?.includes('npmjs')) return null;
  const m = app.url.match(/npmjs\.com\/package\/([^/?#]+)/);
  return m ? m[1] : null;
}

async function fetchNpm(pkgName) {
  try {
    const res = await fetch(`${NPM_API}/${pkgName}`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return null;
    const data = await res.json();
    return {
      exists: true,
      version: data['dist-tags']?.latest,
      description: data.description,
      license: data.license,
    };
  } catch {
    return null;
  }
}

// ── Format for scorer prompt ─────────────────────────────────────────────────

export function formatEnrichmentForScorer(enriched, testResults) {
  const lines = ['## Quantitative data for scoring (use these numbers in justifications)\n'];

  // Container test results
  lines.push('### Container test results');
  lines.push(`- Install success: ${testResults.install_success}`);
  lines.push(`- Install time: ${testResults.install_time_s}s`);
  lines.push(`- Tests passed: ${testResults.tests_passed} / ${testResults.tests_total}`);
  lines.push(`- Basic run success: ${testResults.basic_run_success}`);

  // Benchmark lines from stdout
  if (testResults.benchmark_notes) {
    lines.push('\n### Benchmark measurements from container');
    testResults.benchmark_notes.split('\n').forEach(l => lines.push(`- ${l.replace('BENCHMARK:', '')}`));
  }

  // GitHub data
  if (enriched.github) {
    const g = enriched.github;
    lines.push('\n### GitHub repository stats');
    lines.push(`- Stars: ${g.stars.toLocaleString()}`);
    lines.push(`- Forks: ${g.forks}`);
    lines.push(`- Open issues: ${g.open_issues}`);
    lines.push(`- Contributors: ${g.contributors}`);
    lines.push(`- License: ${g.license}`);
    lines.push(`- Days since last commit: ${g.days_since_update}`);
    lines.push(`- Days since repo created: ${g.days_since_created}`);
    lines.push(`- Is a fork: ${g.is_fork}`);
    lines.push(`- Primary language: ${g.language || 'unknown'}`);
  } else {
    lines.push('\n### GitHub repository stats');
    lines.push('- No GitHub repo detected or API unavailable');
  }

  // Similar tools comparison
  if (enriched.similar_github?.length) {
    lines.push('\n### Similar tools — GitHub stars (for differentiation and community comparison)');
    enriched.similar_github.forEach(t => {
      lines.push(`- ${t.name}: ${t.stars.toLocaleString()} stars (${t.repo})`);
    });
    if (enriched.github) {
      const appStars = enriched.github.stars;
      enriched.similar_github.forEach(t => {
        const diff = appStars - t.stars;
        const pct = t.stars > 0 ? Math.round((diff / t.stars) * 100) : 0;
        lines.push(`  → vs ${t.name}: ${diff >= 0 ? '+' : ''}${diff} stars (${pct >= 0 ? '+' : ''}${pct}%)`);
      });
    }
  }

  // PyPI
  if (enriched.pypi?.exists) {
    lines.push('\n### PyPI package');
    lines.push(`- Package exists: yes (v${enriched.pypi.version})`);
    lines.push(`- Python requirement: ${enriched.pypi.requires_python || 'any'}`);
  } else {
    lines.push('\n### PyPI package');
    lines.push('- No PyPI package found — not pip-installable');
  }

  return lines.join('\n');
}
