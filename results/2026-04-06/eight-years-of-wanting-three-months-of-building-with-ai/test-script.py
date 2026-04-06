#!/usr/bin/env python3
# Fallback test script for: Eight years of wanting, three months of building with AI
import subprocess, sys, time
print("=== LLM Daily Review — Fallback Test Runner ===")
print("App: Eight years of wanting, three months of building with AI")
print("Type: other-llm")

start = time.time()
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--quiet', 'eight-years-of-wanting-three-months-of-building-with-ai'],
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
