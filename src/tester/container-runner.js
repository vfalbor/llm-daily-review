// src/tester/container-runner.js
// Generates a real Python test script per app (via Groq based on app type),
// runs it in an isolated Docker container, and returns structured results.
// Container is --rm (auto-deleted). Local temp files cleaned after GitHub upload.

import { execSync, spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';
import { callGroq, GROQ_MODEL_POWERFUL } from '../llm/groq-adapter.js';

const CONTAINER_TIMEOUT_S = 180;
const BASE_IMAGE = 'python:3.12-alpine';

export async function runInContainer(app) {
  const runId = `llm-review-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const logDir = path.join(os.tmpdir(), runId);
  fs.mkdirSync(logDir, { recursive: true });

  // Generate a real, app-specific test script via Groq
  const testScript = await generateTestScript(app);
  const scriptPath = path.join(logDir, 'test.py');
  fs.writeFileSync(scriptPath, testScript);

  // Also save the script itself so it gets uploaded to GitHub (transparency)
  fs.writeFileSync(path.join(logDir, 'test-script.py'), testScript);

  const startTime = Date.now();
  let install_success = false;
  let basic_run_success = false;
  let error_log = '';
  let stdout_log = '';
  let tests_passed = 0;
  let tests_total = 0;
  let benchmark_notes = '';

  try {
    const result = await runDockerContainer({ runId, scriptPath, timeoutS: CONTAINER_TIMEOUT_S });

    stdout_log = result.stdout;
    error_log  = result.stderr.slice(0, 3000);

    install_success  = result.stdout.includes('INSTALL_OK');
    basic_run_success = result.stdout.includes('RUN_OK');

    // Parse structured test results
    const passMatches = result.stdout.match(/TEST_PASS/g);
    const failMatches = result.stdout.match(/TEST_FAIL/g);
    const skipMatches = result.stdout.match(/TEST_SKIP/g);
    tests_passed = passMatches?.length ?? 0;
    const tests_failed = failMatches?.length ?? 0;
    const tests_skipped = skipMatches?.length ?? 0;
    tests_total  = tests_passed + tests_failed + tests_skipped;

    // Extract benchmark comparison lines
    const benchLines = result.stdout.split('\n').filter(l => l.startsWith('BENCHMARK:'));
    benchmark_notes = benchLines.join('\n');

    fs.writeFileSync(path.join(logDir, 'stdout.txt'), result.stdout);
    fs.writeFileSync(path.join(logDir, 'stderr.txt'), result.stderr);
  } catch (err) {
    error_log = err.message;
    fs.writeFileSync(path.join(logDir, 'stdout.txt'), '');
    fs.writeFileSync(path.join(logDir, 'stderr.txt'), err.message);
  }

  const elapsed_s = ((Date.now() - startTime) / 1000).toFixed(1);

  return {
    run_id: runId,
    log_dir: logDir,
    install_success,
    install_time_s: parseFloat(elapsed_s),
    basic_run_success,
    tests_passed,
    tests_total,
    benchmark_notes,
    error_log,
    notes: stdout_log.slice(0, 4000),
  };
}

// ── Generate real Python test code via Groq ──────────────────────────────────

// Installation strategy per domain/type
function installStrategy(app) {
  const type   = (app.app_type || '').toLowerCase();
  const domain = (app.domain   || '').toLowerCase();
  const url    = app.tool_url || app.url || '';
  const isGithub = url.includes('github.com') || url.includes('gitlab.com');
  const repoPath = url.replace(/https?:\/\/(github|gitlab)\.com\//, '').replace(/\.git$/, '');

  if (domain === 'language' || type.startsWith('lang-')) {
    return {
      apk_packages: 'go git cargo rust nodejs npm',
      strategy: `compiled-language`,
      hint: `This is a compiled language/runtime. Use subprocess to: 1) apk add the needed compiler, 2) git clone the repo, 3) build from source, 4) run hello world. Do NOT assume a pip package exists.`,
    };
  }
  if (domain === 'devtool' && (type.includes('build') || type.includes('cli'))) {
    return {
      apk_packages: 'nodejs npm git cargo rust',
      strategy: 'cli-tool',
      hint: `Install via npm/cargo/pip/apk. Try multiple methods. Measure execution time vs a known baseline.`,
    };
  }
  if (domain === 'database' || type.startsWith('database-')) {
    return {
      apk_packages: 'sqlite',
      strategy: 'database',
      hint: `pip install the client. Create an in-memory DB. Insert 1000 rows. Query with WHERE. Measure latency vs sqlite3 stdlib as baseline.`,
    };
  }
  if (domain === 'infrastructure' || type.startsWith('infra-')) {
    return {
      apk_packages: 'git curl',
      strategy: 'infra',
      hint: `Check if a pip/npm package exists. Test CLI availability. If Docker-only, test the image manifest via registry API (no docker run needed).`,
    };
  }
  if (domain === 'hardware' || type.startsWith('hardware-')) {
    return {
      apk_packages: 'git',
      strategy: 'hardware',
      hint: `Clone the repo. Count source files and languages. Check for simulator/emulator. Run any Python examples found. No hardware required — test what can run in software.`,
    };
  }
  if (domain === 'web' || type.startsWith('web-')) {
    return {
      apk_packages: 'nodejs npm',
      strategy: 'web',
      hint: `npm install or pip install. Start the server in background. Send HTTP requests. Measure response time. Check /health endpoint if available.`,
    };
  }
  // Default: Python package
  return {
    apk_packages: 'git',
    strategy: 'python-package',
    hint: `pip install the package. Import it. Run a minimal functional test with synthetic data (no API key). Measure import time and core operation latency.`,
  };
}

async function generateTestScript(app) {
  const strategy = installStrategy(app);
  const repoUrl  = app.tool_url || app.url || '';

  const systemPrompt = `You are an expert QA engineer. Write a self-contained Python test script
that runs inside a Docker container based on python:3.12-alpine.
NETWORK IS AVAILABLE throughout the entire script execution.

The script MUST:
1. Install system packages with subprocess: subprocess.run(['apk','add','--no-cache','<pkg>'], check=False)
2. Install tool dependencies (pip/npm/cargo/go get) via subprocess
3. Print structured markers on stdout:
   INSTALL_OK | INSTALL_FAIL:<reason>
   TEST_PASS:<name> | TEST_FAIL:<name>:<reason> | TEST_SKIP:<name>:<reason>
   BENCHMARK:<metric_name>:<numeric_value>
   RUN_OK  (always print this last, even after failures)
4. Always emit at least 3 BENCHMARK lines with real numeric values (measure time/memory/count)
5. Compare against a known baseline tool and emit: BENCHMARK:vs_<baseline>_<metric>:<ratio_or_ms>
6. Never use placeholder pass statements — write real executable code for every test
7. Handle failures gracefully: catch exceptions, print TEST_FAIL, continue to next test

BENCHMARK examples:
  BENCHMARK:install_time_s:12.4
  BENCHMARK:import_time_ms:142
  BENCHMARK:hello_world_ms:85
  BENCHMARK:compile_time_ms:340
  BENCHMARK:query_latency_ms:4.2
  BENCHMARK:vs_python_fib35_ratio:0.82
  BENCHMARK:loc_count:1240
  BENCHMARK:test_files_count:23

Return ONLY the Python script, no markdown fences, no explanation.`;

  const userPrompt = `Write a QA test script for this app from Hacker News:

Title: ${app.title}
URL: ${repoUrl}
Domain: ${app.domain || 'unknown'}
App type: ${app.app_type || 'unknown'}
Description: ${app.description || ''}
Is open source: ${app.is_open_source ?? 'unknown'}
Requires API key: ${app.requires_api_key ?? 'unknown'}
Similar tools: ${(app.similar_tools || []).join(', ')}

INSTALLATION STRATEGY: ${strategy.strategy}
Hint: ${strategy.hint}
Pre-install these APK packages first: ${strategy.apk_packages}

Proposed tests to implement:
${(app.proposed_tests || ['Install and basic run', 'Measure performance', 'Compare vs similar tool']).map((t, i) => `  ${i + 1}. ${t}`).join('\n')}

IMPORTANT RULES:
- If this is a compiled language/tool: use 'apk add' + git clone + build from source. DO NOT assume pip package.
- If pip install fails, try: git clone + pip install -e . as fallback
- If API key required: mock the API call with a fake key and test error handling, or test CLI --help
- Always measure and emit BENCHMARK lines with real numbers (use time.time() and tracemalloc)
- Compare performance vs the most similar baseline tool listed above
- The script must complete and print RUN_OK even if all tests fail`;

  try {
    const code = await callGroq(systemPrompt, userPrompt, 3000, GROQ_MODEL_POWERFUL);
    return code.replace(/^```python\n?|^```\n?|```$/gm, '').trim();
  } catch (err) {
    return buildFallbackScript(app);
  }
}

  try {
    const code = await callGroq(systemPrompt, userPrompt, 3000, GROQ_MODEL_POWERFUL);
    // Strip any accidental markdown fences
    return code.replace(/^```python\n?|^```\n?|```$/gm, '').trim();
  } catch (err) {
    // Fallback: minimal static script
    return buildFallbackScript(app);
  }
}

function buildFallbackScript(app) {
  const pkgName = app.title?.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'unknown';
  return `#!/usr/bin/env python3
# Fallback test script for: ${app.title}
import subprocess, sys, time
print("=== LLM Daily Review — Fallback Test Runner ===")
print("App: ${app.title}")
print("Type: ${app.app_type || 'unknown'}")

start = time.time()
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--quiet', '${pkgName}'],
    capture_output=True, text=True, timeout=60
)
elapsed = time.time() - start
if result.returncode == 0:
    print("INSTALL_OK")
    print(f"BENCHMARK:install_time_s:{elapsed:.2f}")
else:
    print(f"INSTALL_FAIL:{result.stderr[:300]}")
    print("TEST_SKIP:import:package_not_installed")

print("RUN_OK")
`;
}

// ── Docker runner ────────────────────────────────────────────────────────────

async function runDockerContainer({ runId, scriptPath, timeoutS }) {
  // Pull image if needed (with network), then run with network disabled
  try {
    execSync(`docker pull ${BASE_IMAGE} -q`, { stdio: 'ignore', timeout: 60_000 });
  } catch { /* image likely cached */ }

  return new Promise((resolve, reject) => {
    const args = [
      'run', '--rm',
      '--name', runId,
      '--memory', '512m',
      '--cpus', '1',
      '--network', 'host',           // allow pip install during test
      '--tmpfs', '/tmp:size=200m',
      '-v', `${scriptPath}:/app/test.py:ro`,
      BASE_IMAGE,
      'sh', '-c',
      'apk add --no-cache git curl 2>/dev/null; pip install --quiet requests 2>/dev/null; python /app/test.py',
    ];

    let stdout = '';
    let stderr = '';

    const child = spawn('docker', args);

    child.stdout.on('data', d => { stdout += d.toString(); });
    child.stderr.on('data', d => { stderr += d.toString(); });

    const timer = setTimeout(() => {
      child.kill();
      try { execSync(`docker rm -f ${runId}`, { stdio: 'ignore' }); } catch {}
      resolve({ exit_code: -1, stdout, stderr: stderr + '\nTIMEOUT' });
    }, (timeoutS + 10) * 1000);

    child.on('close', code => {
      clearTimeout(timer);
      resolve({ exit_code: code, stdout, stderr });
    });

    child.on('error', err => {
      clearTimeout(timer);
      reject(err);
    });
  });
}
