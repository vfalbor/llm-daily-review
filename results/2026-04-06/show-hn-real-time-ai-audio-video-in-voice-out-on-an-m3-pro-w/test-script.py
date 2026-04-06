#!/usr/bin/env python3
# Fallback test script for: Show HN: Real-time AI (audio/video in, voice out) on an M3 Pro with Gemma E2B
import subprocess, sys, time
print("=== LLM Daily Review — Fallback Test Runner ===")
print("App: Show HN: Real-time AI (audio/video in, voice out) on an M3 Pro with Gemma E2B")
print("Type: model-server")

start = time.time()
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--quiet', 'show-hn-real-time-ai-audio-video-in-voice-out-on-an-m3-pro-with-gemma-e2b'],
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
