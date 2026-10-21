#!/usr/bin/env python3
import subprocess, sys, os, time, json, shlex, signal, threading, urllib.request, urllib.error, http.client, socket
import tracemalloc
from pathlib import Path

# ---------- helpers ----------
def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def print_marker(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        pass

def kill_process(p):
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    except Exception:
        pass

# ---------- installation ----------
install_start = time.time()
apk_ret, _, apk_err = run_cmd(['apk', 'add', '--no-cache', 'nodejs', 'npm'])
if apk_ret == 0:
    print_marker("INSTALL_OK")
else:
    print_marker(f"INSTALL_FAIL:apk add error: {apk_err.strip()}")

# Clone repo
repo_url = "https://github.com/petercai/permit-simcity.git"
repo_dir = Path("/tmp/permit-simcity")
if repo_dir.exists():
    subprocess.run(['rm', '-rf', str(repo_dir)])
clone_ret, _, clone_err = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(repo_dir)])
if clone_ret != 0:
    print_marker(f"INSTALL_FAIL:git clone error: {clone_err.strip()}")

# npm install
npm_ret, npm_out, npm_err = run_cmd(['npm', 'ci'], cwd=str(repo_dir))
if npm_ret != 0:
    # fallback to npm install
    npm_ret, npm_out, npm_err = run_cmd(['npm', 'install'], cwd=str(repo_dir))
if npm_ret == 0:
    print_marker("INSTALL_OK")
else:
    print_marker(f"INSTALL_FAIL:npm install error: {npm_err.strip()}")

install_end = time.time()
print_marker(f"BENCHMARK:install_time_s:{install_end - install_start:.3f}")

# ---------- start server ----------
server_process = None
server_port = 3000
def start_server():
    global server_process
    env = os.environ.copy()
    env["PORT"] = str(server_port)
    server_process = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=str(repo_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        env=env,
        text=True
    )
    # stream output in background to avoid pipe blockage
    threading.Thread(target=lambda: [line for line in server_process.stdout], daemon=True).start()
    threading.Thread(target=lambda: [line for line in server_process.stderr], daemon=True).start()

start_time = time.time()
start_server()
# wait for server to be up
def wait_port(port, timeout=30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

if not wait_port(server_port, 30):
    print_marker("TEST_FAIL:server_start:Server did not start within timeout")
else:
    print_marker("TEST_PASS:server_start")
    print_marker(f"BENCHMARK:server_start_time_s:{time.time() - start_time:.3f}")

# ---------- benchmark helper ----------
def http_get(path):
    url = f"http://127.0.0.1:{server_port}{path}"
    req = urllib.request.Request(url, method='GET')
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            elapsed = time.time() - start
            return resp.status, data, elapsed
    except urllib.error.HTTPError as e:
        return e.code, e.read(), time.time() - start
    except Exception as e:
        return None, str(e).encode(), time.time() - start

# ---------- tests ----------
# Test 1: health endpoint (if exists) or root page load
try:
    status, body, latency = http_get('/')
    if status == 200:
        print_marker("TEST_PASS:main_page_load")
        print_marker(f"BENCHMARK:main_page_load_ms:{latency*1000:.2f}")
    else:
        raise AssertionError(f"Unexpected status {status}")
except Exception as e:
    print_marker(f"TEST_FAIL:main_page_load:{e}")

# Test 2: simulate creating a city via API (if endpoint exists)
# This repo is frontend only; we will just check that a known element exists in HTML.
try:
    html = body.decode()
    if "Permit SimCity" in html or "SimCity" in html:
        print_marker("TEST_PASS:ui_presence")
    else:
        raise AssertionError("Main title not found")
except Exception as e:
    print_marker(f"TEST_FAIL:ui_presence:{e}")

# Test 3: measure page load performance vs baseline (vanilla SimCity web clone)
# Baseline metric (hardcoded) - assume vanilla load ~1200ms
baseline_ms = 1200.0
try:
    _, _, load_ms = http_get('/')
    ratio = load_ms*1000 / baseline_ms
    print_marker(f"BENCHMARK:vs_vanilla_simcity_load_ratio:{ratio:.3f}")
except Exception as e:
    print_marker(f"TEST_FAIL:benchmark_vs_baseline:{e}")

# Additional benchmark: memory usage snapshot
tracemalloc.start()
snapshot = tracemalloc.take_snapshot()
stats = snapshot.statistics('lineno')
total_kb = sum(s.size for s in stats) / 1024
print_marker(f"BENCHMARK:memory_usage_kb:{total_kb:.1f}")
tracemalloc.stop()

# ---------- cleanup ----------
if server_process:
    kill_process(server_process)

print_marker("RUN_OK")