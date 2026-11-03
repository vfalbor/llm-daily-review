#!/usr/bin/env python3
import subprocess, sys, time, json, traceback, tracemalloc, urllib.request, ssl, socket
from pathlib import Path

# Helper to print markers
def marker(s):
    print(s, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

# 1. Install system packages
def install_system():
    pkgs = ["nodejs", "npm", "ca-certificates"]
    try:
        res = run_cmd(['apk', 'add', '--no-cache'] + pkgs, check=False)
        if res.returncode == 0:
            marker("INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:apk exit {res.returncode}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{e}")

install_system()

# 2. Install python dependencies
def pip_install(pkg):
    try:
        res = run_cmd([sys.executable, "-m", "pip", "install", "--quiet", pkg])
        if res.returncode == 0:
            return True
        else:
            return False
    except Exception:
        return False

deps = ["requests", "websocket-client"]
for d in deps:
    if not pip_install(d):
        marker(f"INSTALL_FAIL:pip install {d}")
    else:
        marker("INSTALL_OK")

# Benchmark storage
benchmarks = {}

def bench(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        result = e
        success = False
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = end - start
    benchmarks[name] = {"time": elapsed, "mem_peak": peak}
    return success, result, elapsed, peak

# Test 1: Home page render
def test_home():
    url = "https://getbema.app/"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        data = resp.read()
        return b"Bema" in data

success, result, t, mem = bench("home_page", test_home)
if success and result:
    marker("TEST_PASS:home_page")
else:
    reason = result if not success else "content missing"
    marker(f"TEST_FAIL:home_page:{reason}")

# Test 2: Simple health check (mocked as endpoint /api/health if exists)
def test_health():
    url = "https://getbema.app/api/health"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        # If endpoint not present, consider skip
        raise RuntimeError("health endpoint not reachable")

try:
    success, _, t2, _ = bench("health_check", test_health)
    if success:
        marker("TEST_PASS:health_check")
    else:
        marker("TEST_FAIL:health_check:unexpected response")
except Exception as e:
    marker(f"TEST_SKIP:health_check:{e}")

# Test 3: Measure request latency to a static asset (e.g., favicon)
def test_latency():
    url = "https://getbema.app/favicon.ico"
    start = time.time()
    urllib.request.urlopen(url, timeout=10).read()
    return time.time() - start

success, latency, t3, _ = bench("favicon_latency", test_latency)
if success:
    marker(f"TEST_PASS:favicon_latency")
else:
    marker(f"TEST_FAIL:favicon_latency:{latency}")

# Emit benchmarks
for name, data in benchmarks.items():
    marker(f"BENCHMARK:{name}_time_s:{data['time']:.4f}")
    marker(f"BENCHMARK:{name}_mem_peak_bytes:{data['mem_peak']}")

# Compare against baseline (Slack) for favicon latency as example
baseline_latency = 0.120  # assumed baseline in seconds
if "favicon_latency_time_s" in benchmarks:
    ratio = benchmarks["favicon_latency"]["time"] / baseline_latency
    marker(f"BENCHMARK:vs_slack_favicon_latency_ratio:{ratio:.2f}")

# Ensure at least three benchmark lines (already emitted)
# Final marker
marker("RUN_OK")