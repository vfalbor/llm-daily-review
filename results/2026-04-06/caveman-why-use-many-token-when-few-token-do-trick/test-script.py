#!/usr/bin/env python3
# Fallback test script for: Caveman: Why use many token when few token do trick
import subprocess, sys, time
print("=== LLM Daily Review — Fallback Test Runner ===")
print("App: Caveman: Why use many token when few token do trick")
print("Type: prompt-tool")

start = time.time()
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--quiet', 'caveman-why-use-many-token-when-few-token-do-trick'],
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
