// src/tester/container-runner.js
// Runs automated tests for each app inside a minimal Docker container.
// Container is deleted automatically after the run.

import { execSync, spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

const CONTAINER_TIMEOUT_S = 120;
const BASE_IMAGE = 'python:3.12-alpine'; // minimal base

export async function runInContainer(app) {
  const runId = `llm-review-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const logDir = path.join(os.tmpdir(), runId);
  fs.mkdirSync(logDir, { recursive: true });

  const testScript = buildTestScript(app);
  const scriptPath = path.join(logDir, 'test.py');
  fs.writeFileSync(scriptPath, testScript);

  const startTime = Date.now();
  let install_success = false;
  let basic_run_success = false;
  let error_log = '';
  let notes = '';

  try {
    // Run container: mount only the test script, no internet after image pull
    const result = await runDockerContainer({
      runId,
      image: BASE_IMAGE,
      scriptPath,
      timeoutS: CONTAINER_TIMEOUT_S,
    });

    install_success = result.exit_code === 0 || result.stdout.includes('INSTALL_OK');
    basic_run_success = result.stdout.includes('RUN_OK');
    error_log = result.stderr.slice(0, 2000); // cap log size
    notes = result.stdout.slice(0, 3000);

    // Save full logs
    fs.writeFileSync(path.join(logDir, 'stdout.txt'), result.stdout);
    fs.writeFileSync(path.join(logDir, 'stderr.txt'), result.stderr);
  } catch (err) {
    error_log = err.message;
    notes = 'Container execution failed';
  }

  const elapsed_s = (Date.now() - startTime) / 1000;

  return {
    run_id: runId,
    log_dir: logDir,
    install_success,
    install_time_s: elapsed_s,
    basic_run_success,
    error_log,
    notes,
  };
}

async function runDockerContainer({ runId, image, scriptPath, timeoutS }) {
  return new Promise((resolve, reject) => {
    const args = [
      'run',
      '--rm',                          // auto-delete after exit
      '--name', runId,
      '--memory', '512m',              // cap memory
      '--cpus', '1',
      '--network', 'none',             // no network after start (tests use cached packages)
      '--read-only',
      '--tmpfs', '/tmp:size=100m',
      '-v', `${scriptPath}:/app/test.py:ro`,
      image,
      'python', '/app/test.py',
    ];

    let stdout = '';
    let stderr = '';

    const child = spawn('docker', args, { timeout: timeoutS * 1000 });

    child.stdout.on('data', d => { stdout += d.toString(); });
    child.stderr.on('data', d => { stderr += d.toString(); });

    const timer = setTimeout(() => {
      child.kill();
      // Force-remove container if still running
      try { execSync(`docker rm -f ${runId}`, { stdio: 'ignore' }); } catch {}
      resolve({ exit_code: -1, stdout, stderr: stderr + '\nTIMEOUT' });
    }, (timeoutS + 5) * 1000);

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

function buildTestScript(app) {
  // Dynamically generate test script based on app type
  const tests = (app.proposed_tests || []).map((t, i) => `
# Test ${i + 1}: ${t}
try:
    # Placeholder — Claude Code fills this in per app
    print(f"TEST_${i + 1}: SKIP (manual implementation needed)")
except Exception as e:
    print(f"TEST_${i + 1}_ERROR: {e}")
`).join('\n');

  return `#!/usr/bin/env python3
# Auto-generated test script for: ${app.title}
# URL: ${app.url}
# App type: ${app.app_type || 'unknown'}
import subprocess, sys, time

print("=== LLM Daily Review Test Runner ===")
print(f"App: ${app.title}")
print(f"Type: ${app.app_type}")

${app.is_open_source && app.repo_url ? `
# Attempt to install if it's a pip package
try:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--quiet', '${app.title.toLowerCase().replace(/\s+/g, '-')}'],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL: {result.stderr[:500]}")
except Exception as e:
    print(f"INSTALL_ERROR: {e}")
` : '# Package install not attempted (closed source or no pip package)'}

${tests}

print("RUN_OK")
`;
}
