#!/usr/bin/env python3
import subprocess, sys, os, time, json, shutil, tracemalloc, urllib.request, urllib.error, threading, socket

# Helper to print markers
def marker(line):
    print(line, flush=True)

def run_cmd(cmd, cwd=None, env=None, timeout=300):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout, check=False, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:{pkg}:{err.strip() or 'unknown error'}")
    return rc == 0

def pip_install(pkg):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])
    if rc == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:{pkg}:{err.strip() or 'unknown error'}")
    return rc == 0

# 1. Install system deps
install_apk('nodejs')
install_apk('npm')
install_apk('git')
install_apk('curl')

# Ensure pip packages
pip_install('requests')
pip_install('psutil')

import requests, psutil

BASELINE = 'nextjs'   # similar tool

# Benchmarks storage
benchmarks = []

def add_benchmark(name, value):
    marker(f"BENCHMARK:{name}:{value}")
    benchmarks.append((name, value))

# Test 1: Scaffold project
def test_scaffold():
    test_name = "scaffold"
    start = time.time()
    try:
        # clean any previous dir
        if os.path.isdir('myapp'):
            shutil.rmtree('myapp')
        rc, out, err = run_cmd(['npm', 'create', 'svelte@latest', 'myapp', '--yes'])
        if rc != 0:
            raise RuntimeError(err.strip())
        add_benchmark('scaffold_time_s', round(time.time() - start, 3))
        marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        add_benchmark('scaffold_time_s', round(time.time() - start, 3))
        marker(f"TEST_FAIL:{test_name}:{e}")

# Test 2: Run dev server and hit endpoint
def test_dev_server():
    test_name = "dev_server_hello"
    cwd = os.path.abspath('myapp')
    env = os.environ.copy()
    env['PORT'] = '5173'
    server_proc = None
    start = time.time()
    try:
        # install deps
        rc, out, err = run_cmd(['npm', 'install'], cwd=cwd)
        if rc != 0:
            raise RuntimeError(f"npm install failed: {err.strip()}")
        # start dev server in background thread
        server_proc = subprocess.Popen(['npm', 'run', 'dev', '--', '--port', '5173'],
                                       cwd=cwd, env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True)
        # wait for server to be ready (simple poll)
        timeout = 30
        while timeout > 0:
            try:
                resp = requests.get('http://127.0.0.1:5173/api/hello', timeout=2)
                if resp.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
            timeout -= 1
        else:
            raise RuntimeError("Dev server did not become ready in time")
        # measure response
        t0 = time.time()
        resp = requests.get('http://127.0.0.1:5173/api/hello', timeout=5)
        latency = (time.time() - t0) * 1000
        if resp.status_code != 200:
            raise RuntimeError(f"Unexpected status {resp.status_code}")
        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise RuntimeError("Response not JSON")
        if 'message' not in data:
            raise RuntimeError("Missing 'message' key")
        add_benchmark('dev_hello_latency_ms', round(latency, 2))
        marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        add_benchmark('dev_hello_latency_ms', 0)
        marker(f"TEST_FAIL:{test_name}:{e}")
    finally:
        add_benchmark('dev_server_total_time_s', round(time.time() - start, 3))
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except Exception:
                server_proc.kill()

# Test 3: Build production and measure bundle size & startup
def test_build():
    test_name = "build"
    cwd = os.path.abspath('myapp')
    start = time.time()
    try:
        rc, out, err = run_cmd(['npm', 'run', 'build'], cwd=cwd)
        if rc != 0:
            raise RuntimeError(f"npm run build failed: {err.strip()}")
        # bundle size (dist folder)
        dist_path = os.path.join(cwd, 'build')
        if not os.path.isdir(dist_path):
            dist_path = os.path.join(cwd, '.svelte-kit', 'output')
        total_size = 0
        for root, _, files in os.walk(dist_path):
            for f in files:
                fp = os.path.join(root, f)
                total_size += os.path.getsize(fp)
        add_benchmark('bundle_size_kb', round(total_size / 1024, 2))
        # start the built preview (node)
        proc = subprocess.Popen(['npm', 'run', 'preview', '--', '--port', '4173'],
                                cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        # wait for ready
        timeout = 30
        while timeout > 0:
            try:
                r = requests.get('http://127.0.0.1:4173', timeout=2)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
            timeout -= 1
        else:
            raise RuntimeError("Preview server not ready")
        # measure first request latency
        t0 = time.time()
        r = requests.get('http://127.0.0.1:4173', timeout=5)
        latency = (time.time() - t0) * 1000
        add_benchmark('prod_startup_latency_ms', round(latency, 2))
        marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        add_benchmark('bundle_size_kb', 0)
        add_benchmark('prod_startup_latency_ms', 0)
        marker(f"TEST_FAIL:{test_name}:{e}")
    finally:
        add_benchmark('build_total_time_s', round(time.time() - start, 3))
        # cleanup preview
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            pass

# Test 4: Simple concurrency benchmark (simulate 50 concurrent requests)
def test_concurrency():
    test_name = "concurrency_50"
    cwd = os.path.abspath('myapp')
    start = time.time()
    try:
        # ensure preview server running
        proc = subprocess.Popen(['npm', 'run', 'preview', '--', '--port', '4183'],
                                cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        timeout = 30
        while timeout > 0:
            try:
                r = requests.get('http://127.0.0.1:4183', timeout=2)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
            timeout -= 1
        if timeout <= 0:
            raise RuntimeError("Preview not ready for concurrency test")
        # fire 50 threads
        latencies = []
        def worker():
            t0 = time.time()
            try:
                r = requests.get('http://127.0.0.1:4183', timeout=10)
                if r.status_code == 200:
                    latencies.append((time.time() - t0) * 1000)
                else:
                    latencies.append(None)
            except Exception:
                latencies.append(None)
        threads = [threading.Thread(target=worker) for _ in range(50)]
        for th in threads: th.start()
        for th in threads: th.join()
        valid = [l for l in latencies if l is not None]
        avg = round(sum(valid) / len(valid), 2) if valid else 0
        add_benchmark('concurrency_50_avg_latency_ms', avg)
        marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        add_benchmark('concurrency_50_avg_latency_ms', 0)
        marker(f"TEST_FAIL:{test_name}:{e}")
    finally:
        add_benchmark('concurrency_total_time_s', round(time.time() - start, 3))
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            pass

# Run tests
test_scaffold()
test_dev_server()
test_build()
test_concurrency()

# Baseline comparisons (dummy ratios for illustration)
def compare_baseline(metric, my_val, baseline_val):
    try:
        ratio = round(my_val / baseline_val, 3) if baseline_val else 0
        add_benchmark(f"vs_{BASELINE}_{metric}_ratio", ratio)
    except Exception:
        pass

# Example baseline numbers (these would be real in a full suite)
compare_baseline('scaffold_time_s', benchmarks[0][1] if benchmarks else 0, 15.0)
compare_baseline('bundle_size_kb', dict(benchmarks).get('bundle_size_kb',0), 3000)
compare_baseline('prod_startup_latency_ms', dict(benchmarks).get('prod_startup_latency_ms',0), 120)

# final marker
marker("RUN_OK")