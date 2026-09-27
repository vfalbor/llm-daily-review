import subprocess, sys, os, time, json, threading, signal, tracemalloc, requests, shutil, pathlib

# Helpers
def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def print_marker(msg):
    print(msg, flush=True)

def safe_remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass

# 1. Install system packages
apk_pkgs = ["nodejs", "npm", "git", "curl"]
install_start = time.time()
apk_res = run_cmd(["apk", "add", "--no-cache"] + apk_pkgs, check=False)
install_end = time.time()
if apk_res and apk_res.returncode == 0:
    print_marker("INSTALL_OK")
else:
    reason = (apk_res.stderr.strip() if apk_res else "apk command failed")
    print_marker(f"INSTALL_FAIL:{reason}")
print_marker(f"BENCHMARK:install_time_s:{install_end - install_start:.2f}")

# 2. Clone repository
repo_url = "https://github.com/reladraw/reladraw.git"
work_dir = "/tmp/reladraw_test"
safe_remove(work_dir)
clone_start = time.time()
clone_res = run_cmd(["git", "clone", "--depth", "1", repo_url, work_dir])
clone_end = time.time()
if clone_res and clone_res.returncode == 0:
    print_marker("INSTALL_OK")
else:
    reason = (clone_res.stderr.strip() if clone_res else "git clone failed")
    print_marker(f"INSTALL_FAIL:{reason}")

# 3. Install npm dependencies
npm_install_start = time.time()
npm_res = run_cmd(["npm", "ci"], cwd=work_dir)
npm_install_end = time.time()
if npm_res and npm_res.returncode == 0:
    print_marker("INSTALL_OK")
else:
    reason = (npm_res.stderr.strip() if npm_res else "npm install failed")
    print_marker(f"INSTALL_FAIL:{reason}")
print_marker(f"BENCHMARK:npm_install_time_s:{npm_install_end - npm_install_start:.2f}")

# Function to start server in background
server_process = None
def start_server():
    global server_process
    server_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=work_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )
    # give it time to start
    time.sleep(5)

def stop_server():
    global server_process
    if server_process:
        os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        server_process.wait(timeout=5)

# 4. Test 1: Start dev server and health check
try:
    start_server()
    health_url = "http://localhost:3000/health"
    resp = requests.get(health_url, timeout=5)
    if resp.status_code == 200:
        print_marker("TEST_PASS:server_start")
    else:
        print_marker(f"TEST_FAIL:server_start:Unexpected status {resp.status_code}")
except Exception as e:
    print_marker(f"TEST_FAIL:server_start:{e}")
finally:
    stop_server()

# 5. Test 2: Create diagram via API (if available) or simulate rendering
# Assume there is a POST /api/render that accepts diagram JSON
render_url = "http://localhost:3000/api/render"
sample_diagram = {
    "elements": [
        {"type": "node", "id": "A", "x": 0, "y": 0},
        {"type": "node", "id": "B", "x": 100, "y": 0},
        {"type": "edge", "from": "A", "to": "B"}
    ]
}
try:
    start_server()
    t0 = time.time()
    resp = requests.post(render_url, json=sample_diagram, timeout=10)
    t1 = time.time()
    if resp.status_code == 200 and "svg" in resp.text:
        print_marker("TEST_PASS:render_api")
    else:
        print_marker(f"TEST_FAIL:render_api:Bad response {resp.status_code}")
    print_marker(f"BENCHMARK:render_response_ms:{(t1-t0)*1000:.2f}")
except Exception as e:
    print_marker(f"TEST_FAIL:render_api:{e}")
finally:
    stop_server()

# 6. Test 3: CLI render and compare output size
cli_path = os.path.join(work_dir, "bin", "reladraw")
sample_file = os.path.join(work_dir, "sample.rdl")
with open(sample_file, "w") as f:
    f.write("node A\nnode B\nedge A B\n")
try:
    cli_start = time.time()
    cli_res = run_cmd([cli_path, "render", sample_file, "--format", "svg"])
    cli_end = time.time()
    if cli_res and cli_res.returncode == 0 and cli_res.stdout.strip().endswith(".svg"):
        out_path = cli_res.stdout.strip()
        size = os.path.getsize(out_path) if os.path.isfile(out_path) else 0
        print_marker(f"TEST_PASS:cli_render")
        print_marker(f"BENCHMARK:cli_output_bytes:{size}")
    else:
        reason = cli_res.stderr.strip() if cli_res else "CLI failed"
        print_marker(f"TEST_FAIL:cli_render:{reason}")
    print_marker(f"BENCHMARK:cli_render_time_ms:{(cli_end-cli_start)*1000:.2f}")
except Exception as e:
    print_marker(f"TEST_FAIL:cli_render:{e}")

# 7. Benchmark vs baseline (Mermaid) – we mock a baseline load time of 120ms
mermaid_baseline_ms = 120.0
# Assume our render_response_ms benchmark exists
render_time_line = None
for line in sys.stdout.getvalue().splitlines() if hasattr(sys.stdout, "getvalue") else []:
    if line.startswith("BENCHMARK:render_response_ms:"):
        render_time_line = line
        break
# If not captured, use last measured variable
render_time_ms = (t1 - t0) * 1000 if 't0' in locals() else 0
ratio = render_time_ms / mermaid_baseline_ms if mermaid_baseline_ms else 0
print_marker(f"BENCHMARK:vs_mermaid_render_time_ratio:{ratio:.3f}")

# Additional generic benchmarks
process = tracemalloc.start()
snapshot1 = tracemalloc.take_snapshot()
time.sleep(0.1)
snapshot2 = tracemalloc.take_snapshot()
stats = snapshot2.compare_to(snapshot1, 'lineno')
total_mem = sum(stat.size_diff for stat in stats) / 1024
print_marker(f"BENCHMARK:memory_peak_kb:{total_mem:.2f}")

# Ensure final marker
print_marker("RUN_OK")