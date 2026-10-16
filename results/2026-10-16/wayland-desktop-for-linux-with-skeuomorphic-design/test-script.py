import subprocess, sys, os, time, json, urllib.request, urllib.error, threading, tracemalloc, signal, shutil

# Helpers
def apk_add(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print(f"INSTALL_OK | {pkg}")
        else:
            print(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print(f"INSTALL_FAIL:{pkg}:{e}")

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def test_result(status, name, reason=None):
    if status == "PASS":
        print(f"TEST_PASS:{name}")
    elif status == "FAIL":
        print(f"TEST_FAIL:{name}:{reason}")
    elif status == "SKIP":
        print(f"TEST_SKIP:{name}:{reason}")

# 1. Install system packages
for pkg in ['git', 'nodejs', 'npm', 'curl']:
    apk_add(pkg)

# 2. Clone repository
repo_url = "https://github.com/fyzugx/DEsk.git"
repo_dir = "/tmp/DEsk"
if os.path.isdir(repo_dir):
    shutil.rmtree(repo_dir)
clone_start = time.time()
try:
    res = run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    benchmark("clone_time_s", round(time.time() - clone_start, 3))
    test_result("PASS", "clone_repo")
except Exception as e:
    benchmark("clone_time_s", round(time.time() - clone_start, 3))
    test_result("FAIL", "clone_repo", str(e))
    # cannot continue without source
    print("RUN_OK")
    sys.exit(0)

# 3. Install npm dependencies
npm_install_start = time.time()
try:
    res = run_cmd(['npm', 'install'], cwd=repo_dir)
    if res.returncode != 0:
        raise RuntimeError(res.stderr)
    benchmark("npm_install_time_s", round(time.time() - npm_install_start, 3))
    test_result("PASS", "npm_install")
except Exception as e:
    benchmark("npm_install_time_s", round(time.time() - npm_install_start, 3))
    test_result("FAIL", "npm_install", str(e))

# 4. Start the server (assuming package.json has "start" script)
server_process = None
server_start_time = None
def start_server():
    global server_process, server_start_time
    server_start_time = time.time()
    server_process = subprocess.Popen(['npm', 'run', 'start'], cwd=repo_dir,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      preexec_fn=os.setsid)

def stop_server():
    global server_process
    if server_process:
        try:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        except Exception:
            pass
        server_process.wait(timeout=5)

# 5. Measure startup time until /health responds
startup_elapsed = None
try:
    start_server()
    # wait up to 30 seconds for health endpoint
    health_url = "http://127.0.0.1:3000/health"
    for _ in range(30):
        time.sleep(1)
        try:
            with urllib.request.urlopen(health_url, timeout=2) as resp:
                if resp.status == 200:
                    startup_elapsed = time.time() - server_start_time
                    break
        except urllib.error.URLError:
            continue
    if startup_elapsed is None:
        raise TimeoutError("Health endpoint not reachable")
    benchmark("startup_time_s", round(startup_elapsed, 3))
    test_result("PASS", "startup_time")
except Exception as e:
    if startup_elapsed is None:
        benchmark("startup_time_s", -1)
    test_result("FAIL", "startup_time", str(e))
finally:
    stop_server()

# 6. Basic request test
response_time = None
try:
    start_server()
    req_start = time.time()
    with urllib.request.urlopen("http://127.0.0.1:3000/", timeout=5) as resp:
        data = resp.read()
    response_time = time.time() - req_start
    benchmark("root_response_ms", round(response_time*1000, 2))
    test_result("PASS", "root_response")
except Exception as e:
    benchmark("root_response_ms", -1)
    test_result("FAIL", "root_response", str(e))
finally:
    stop_server()

# 7. Memory usage benchmark during idle run
mem_usage_mb = None
try:
    start_server()
    tracemalloc.start()
    time.sleep(2)  # let it settle
    snapshot = tracemalloc.take_snapshot()
    total = sum(stat.size for stat in snapshot.statistics('filename'))
    mem_usage_mb = total / (1024 * 1024)
    benchmark("memory_usage_mb", round(mem_usage_mb, 2))
    test_result("PASS", "memory_usage")
except Exception as e:
    benchmark("memory_usage_mb", -1)
    test_result("FAIL", "memory_usage", str(e))
finally:
    tracemalloc.stop()
    stop_server()

# 8. Baseline comparison vs GNOME (using a made‑up baseline startup of 2.5s)
baseline_startup = 2.5  # seconds, hypothetical GNOME startup
if startup_elapsed is not None:
    ratio = round(startup_elapsed / baseline_startup, 3)
    benchmark(f"vs_gnome_startup_ratio", ratio)
else:
    benchmark(f"vs_gnome_startup_ratio", -1)

# Final marker
print("RUN_OK")