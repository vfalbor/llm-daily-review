import subprocess, sys, os, time, json, urllib.request, threading, tracemalloc, shlex, signal, pathlib, re, statistics

REPO_URL = "https://github.com/xiffy/lfm-rss.git"
REPO_DIR = "/tmp/lfm-rss"
TEST_USER = "testuser"
API_KEY = "FAKE_API_KEY"
BASELINE_TOOL = "Last.fm-Feed"  # placeholder baseline name

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkgs):
    try:
        start = time.time()
        result = subprocess.run(['apk', 'add', '--no-cache'] + pkgs, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{result.stderr.strip()}")
        print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def clone_repo():
    try:
        start = time.time()
        if os.path.isdir(REPO_DIR):
            subprocess.run(['rm', '-rf', REPO_DIR], check=False)
        result = run_cmd(['git', 'clone', REPO_URL, REPO_DIR])
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:git clone error {result.stderr.strip()}")
        print_marker(f"BENCHMARK:git_clone_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def npm_install():
    try:
        start = time.time()
        result = run_cmd(['npm', 'install'], cwd=REPO_DIR)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:npm install error {result.stderr.strip()}")
        print_marker(f"BENCHMARK:npm_install_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def start_server():
    try:
        env = os.environ.copy()
        env["LASTFM_API_KEY"] = API_KEY
        proc = subprocess.Popen(['npm', 'start'], cwd=REPO_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
        # give server time to start
        time.sleep(5)
        if proc.poll() is None:
            print_marker("INSTALL_OK")
            return proc
        else:
            out, err = proc.communicate()
            print_marker(f"INSTALL_FAIL:server exited early {err.strip()}")
            return None
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return None

def stop_server(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass

def http_get(path):
    url = f"http://127.0.0.1:3000{path}"
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read().decode()
        elapsed = (time.time() - start) * 1000  # ms
        return data, elapsed
    except Exception as e:
        return None, None

def test_health():
    try:
        data, elapsed = http_get("/health")
        if data is not None:
            print_marker(f"TEST_PASS:health_endpoint")
        else:
            print_marker(f"TEST_FAIL:health_endpoint:No response")
        print_marker(f"BENCHMARK:health_latency_ms:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:health_endpoint:{e}")

def test_feed():
    try:
        data, elapsed = http_get(f"/feed?user={TEST_USER}")
        if data is None:
            print_marker(f"TEST_FAIL:feed_endpoint:No response")
            return
        # simple XML check
        items = re.findall(r"<item>(.*?)</item>", data, re.DOTALL)
        if len(items) == 0:
            print_marker(f"TEST_FAIL:feed_endpoint:No <item> found")
        else:
            print_marker(f"TEST_PASS:feed_endpoint")
        print_marker(f"BENCHMARK:feed_latency_ms:{elapsed:.2f}")
        print_marker(f"BENCHMARK:feed_item_count:{len(items)}")
    except Exception as e:
        print_marker(f"TEST_FAIL:feed_endpoint:{e}")

def load_test(concurrency=20, runs=5):
    latencies = []
    def worker():
        _, elapsed = http_get(f"/feed?user={TEST_USER}")
        if elapsed is not None:
            latencies.append(elapsed)

    try:
        start = time.time()
        threads = []
        for _ in range(concurrency * runs):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        total_time = time.time() - start
        if latencies:
            avg = statistics.mean(latencies)
            print_marker(f"TEST_PASS:load_test")
            print_marker(f"BENCHMARK:load_avg_latency_ms:{avg:.2f}")
            print_marker(f"BENCHMARK:load_total_time_s:{total_time:.2f}")
        else:
            print_marker(f"TEST_FAIL:load_test:No successful requests")
    except Exception as e:
        print_marker(f"TEST_FAIL:load_test:{e}")

def baseline_comparison():
    # dummy baseline numbers for illustration
    baseline_feed_latency = 150.0  # ms
    our_latency = 0.0
    # retrieve last measured feed latency from env variable if set
    # for simplicity reuse the last printed value via a file
    try:
        with open("/tmp/last_feed_latency.txt") as f:
            our_latency = float(f.read().strip())
    except Exception:
        our_latency = None
    if our_latency:
        ratio = our_latency / baseline_feed_latency
        print_marker(f"BENCHMARK:vs_{BASELINE_TOOL}_feed_latency_ratio:{ratio:.2f}")

def main():
    # 1. install system packages
    install_apk(['nodejs', 'npm', 'git', 'bash'])

    # 2. clone repo
    clone_repo()

    # 3. npm install
    npm_install()

    # 4. start server
    server_proc = start_server()
    if not server_proc:
        print_marker("TEST_SKIP:server_start:Unable to start")
    else:
        # health check (optional)
        test_health()
        # feed endpoint test
        test_feed()
        # load test
        load_test()
        # stop server
        stop_server(server_proc)

    # baseline comparison
    baseline_comparison()

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()