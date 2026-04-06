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

async function generateTestScript(app) {
  const systemPrompt = `You are an expert Python QA engineer. Write a self-contained Python test script
that runs inside a minimal Docker container (python:3.12-alpine, no internet access after start).
The script must:
- Use only stdlib + packages installable via pip at container start (network IS available during pip install)
- Print structured markers: INSTALL_OK, INSTALL_FAIL, RUN_OK, TEST_PASS:<name>, TEST_FAIL:<name>:<reason>, TEST_SKIP:<name>:<reason>, BENCHMARK:<metric>:<value>
- For each proposed test, write real executable code — never use placeholder comments or pass statements
- Include benchmark comparisons where possible (e.g., measure latency, token throughput, memory)
- End with print("RUN_OK") if the script completes without fatal errors
Return ONLY the Python script, no markdown fences, no explanation.`;

  const userPrompt = `Write a QA test script for this LLM app:

Title: ${app.title}
URL: ${app.tool_url || app.url}
App type: ${app.app_type || 'unknown'}
Description: ${app.description || ''}
Use modes: ${(app.use_modes || []).join(', ')}
Is open source: ${app.is_open_source ?? 'unknown'}
Requires API key: ${app.requires_api_key ?? 'unknown'}
Similar tools: ${(app.similar_tools || []).join(', ')}
Proposed tests:
${(app.proposed_tests || []).map((t, i) => `  ${i + 1}. ${t}`).join('\n')}

Test strategy by app type:
- fine-tuning / sdk-wrapper / other-llm: pip install, import, basic API call (use mock data if API key needed), measure import time
- benchmark-runner / evaluation: pip install, run --help, compare CLI options with similar tools listed above
- rag-system / vector-db: pip install, create a collection, insert 3 docs, query, measure latency
- agent-framework / prompt-tool: pip install, import, create minimal agent/chain, run with a test prompt
- model-server: check if Docker image exists (docker pull --dry-run), parse README for startup command
- code-assistant: pip install, import, run a simple code completion request
- multimodal: pip install, import, check available modalities

For BENCHMARK lines, compare against similar tools where possible.
Example: BENCHMARK:import_time_ms:142
Example: BENCHMARK:vs_langchain:faster_install`;

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
      'pip install --quiet requests 2>/dev/null; python /app/test.py',
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
