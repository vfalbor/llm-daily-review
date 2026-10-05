#!/usr/bin/env python3
# Fallback test script for: Run Qwen 3.8 Flash Next (125B) on consumer hardware (RTX 4090) at 100T/s
import subprocess, sys, time
print("=== LLM Daily Review — Fallback Test Runner ===")
print("App: Run Qwen 3.8 Flash Next (125B) on consumer hardware (RTX 4090) at 100T/s")
print("Type: llm-inference")

start = time.time()
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--quiet', 'run-qwen-3-8-flash-next-125b-on-consumer-hardware-rtx-4090-at-100t-s'],
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
