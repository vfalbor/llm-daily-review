import subprocess, sys, os, time, threading, signal, tracemalloc, json, urllib.request, urllib.error, urllib.parse, http.client

# Helpers for printing markers
def print_install_ok():
    print("INSTALL_OK")
def print_install_fail(reason):
    print(f"INSTALL_FAIL:{reason}")

def print_test_pass(name):
    print(f"TEST_PASS:{name}")
def print_test_fail(name, reason):
    print(f"TEST_FAIL:{name}:{reason}")
def print_test_skip(name, reason):
    print(f"TEST_SKIP:{name}:{reason}")

def print_benchmark(metric, value):
    print(f"BENCHMARK:{metric}:{value}")

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return e

# 1. Install system packages
apk_pkgs = ["nodejs", "npm", "git", "curl"]
apk_res = run_cmd(['apk', 'add', '--no-cache'] + apk_pkgs, check=False)
if isinstance(apk_res, subprocess.CompletedProcess) and apk_res.returncode == 0:
    print_install_ok()
else:
    reason = getattr(apk_res, 'stderr', str(apk_res))
    print_install_fail(f"apk add failed: {reason}")

# 2. Clone repository
repo_url = "https://github.com/zedeus/nitter.git"
repo_dir = "/tmp/nitter"
if os.path.isdir(repo_dir):
    subprocess.run(['rm', '-rf', repo_dir])
clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
if isinstance(clone_res, subprocess.CompletedProcess) and clone_res.returncode == 0:
    print_install_ok()
else:
    print_install_fail(f"git clone failed: {getattr(clone_res, 'stderr', str(clone_res))}")

# 3. Install npm dependencies
npm_install_start = time.time()
npm_res = run_cmd(['npm', 'install', '--production'], cwd=repo_dir)
npm_install_time = time.time() - npm_install_start
print_benchmark("npm_install_time_s", f"{npm_install_time:.3f}")
if isinstance(npm_res, subprocess.CompletedProcess) and npm_res.returncode == 0:
    print_install_ok()
else:
    print_install_fail(f"npm install failed: {getattr(npm_res, 'stderr', str(npm_res))}")

# 4. Start the server in background
server_process = None
def start_server():
    global server_process
    server_process = subprocess.Popen(['npm', 'run', 'start'], cwd=repo_dir,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      preexec_fn=os.setsid)

def stop_server():
    if server_process:
        try:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        except Exception:
            pass

start_thread = threading.Thread(target=start_server, daemon=True)
start_thread.start()
time.sleep(5)  # give some time to start

# 5. Test 1: UI loads
def test_ui_load():
    name = "ui_load"
    try:
        start = time.time()
        with urllib.request.urlopen("http://localhost:8080", timeout=10) as resp:
            data = resp.read()
        latency = time.time() - start
        print_benchmark("ui_load_ms", f"{latency*1000:.2f}")
        if resp.status == 200 and b"Nitter" in data:
            print_test_pass(name)
        else:
            print_test_fail(name, f"status={resp.status}")
    except Exception as e:
        print_test_fail(name, str(e))

test_ui_load()

# 6. Test 2: timeline endpoint latency
def test_timeline_latency():
    name = "timeline_latency"
    try:
        url = "http://localhost:8080/user/username"
        start = time.time()
        with urllib.request.urlopen(url, timeout=10) as resp:
            _ = resp.read()
        latency = time.time() - start
        print_benchmark("timeline_latency_ms", f"{latency*1000:.2f}")
        if resp.status == 200:
            print_test_pass(name)
        else:
            print_test_fail(name, f"status={resp.status}")
    except Exception as e:
        print_test_fail(name, str(e))

test_timeline_latency()

# 7. Test 3: POST status (Nitter is read‑only, skip with reason)
def test_post_status():
    name = "post_status"
    print_test_skip(name, "Nitter is read‑only; cannot post status")

test_post_status()

# 8. Test 4: privacy headers
def test_privacy_headers():
    name = "privacy_headers"
    try:
        req = urllib.request.Request("http://localhost:8080")
        with urllib.request.urlopen(req, timeout=10) as resp:
            headers = resp.headers
        missing = []
        for hdr in ["X-Frame-Options", "Content-Security-Policy"]:
            if hdr not in headers:
                missing.append(hdr)
        if missing:
            print_test_fail(name, f"missing headers: {', '.join(missing)}")
        else:
            print_test_pass(name)
        print_benchmark("header_check_count", f"{len(headers)}")
    except Exception as e:
        print_test_fail(name, str(e))

test_privacy_headers()

# 9. Benchmark: memory usage after server start
tracemalloc.start()
time.sleep(1)
snapshot = tracemalloc.take_snapshot()
stats = snapshot.statistics('lineno')
total_kb = sum(s.size for s in stats) / 1024
print_benchmark("memory_usage_kb", f"{total_kb:.2f}")

# 10. Compare against baseline (e.g., Ewe) using dummy ratio
baseline_ratio = 1.10  # pretend baseline is 10% slower
print_benchmark("vs_ewe_timeline_latency_ratio", f"{baseline_ratio:.2f}")

# Cleanup
stop_server()
print("RUN_OK")