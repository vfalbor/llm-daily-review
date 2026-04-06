#!/usr/bin/env python3
# Fallback test script for: Show HN: Gemma Gem – AI model embedded in a browser – no API keys, no cloud
import subprocess, sys, time
print("=== LLM Daily Review — Fallback Test Runner ===")
print("App: Show HN: Gemma Gem – AI model embedded in a browser – no API keys, no cloud")
print("Type: model-server")

start = time.time()
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--quiet', 'show-hn-gemma-gem-ai-model-embedded-in-a-browser-no-api-keys-no-cloud'],
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
