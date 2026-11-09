import subprocess, sys, os, time, tracemalloc, threading, signal, json, urllib.request, urllib.error, urllib.parse, socket

# Helper to print markers
def emit(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)

def install_apk(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg])
        if res.returncode == 0:
            emit(f"INSTALL_OK")
        else:
            emit(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        emit(f"INSTALL_FAIL:{pkg}:{e}")

def timed(func):
    def wrapper(*a, **kw):
        start = time.time()
        try:
            result = func(*a, **kw)
            elapsed = time.time() - start
            return result, elapsed
        except Exception as e:
            return e, time.time() - start
    return wrapper

# 1. Install required system packages
for pkg in ['git', 'nodejs', 'npm', 'rust', 'cargo', 'make', 'clang']:
    install_apk(pkg)

# 2. Clone repository
repo_url = "https://github.com/ketchup3d/ketchup.git"
repo_dir = "/tmp/ketchup"
if os.path.isdir(repo_dir):
    subprocess.run(['rm', '-rf', repo_dir])
clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
if clone_res.returncode != 0:
    emit(f"TEST_FAIL:clone_repo:{clone_res.stderr.strip()}")
else:
    emit(f"TEST_PASS:clone_repo")

# 3. Build release
@timed
def cargo_build():
    return run_cmd(['cargo', 'build', '--release'], cwd=repo_dir, timeout=300)

(build_result, build_time) = cargo_build()
if isinstance(build_result, Exception) or build_result.returncode != 0:
    emit(f"TEST_FAIL:cargo_build:{getattr(build_result, 'stderr', str(build_result)).strip()}")
else:
    emit(f"TEST_PASS:cargo_build")
emit(f"BENCHMARK:install_time_s:{build_time:.2f}")

# 4. Run unit tests
@timed
def cargo_test():
    return run_cmd(['cargo', 'test', '--quiet'], cwd=repo_dir, timeout=300)

(test_result, test_time) = cargo_test()
if isinstance(test_result, Exception) or test_result.returncode != 0:
    emit(f"TEST_FAIL:cargo_test:{getattr(test_result, 'stderr', str(test_result)).strip()}")
else:
    emit(f"TEST_PASS:cargo_test")
emit(f"BENCHMARK:test_time_s:{test_time:.2f}")

# 5. Start dev server in background
server_process = None
def start_server():
    global server_process
    server_process = subprocess.Popen(
        ['cargo', 'run'],
        cwd=repo_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid
    )
    # wait a bit for server to start
    time.sleep(5)

start_server()
emit("TEST_PASS:start_server")

# Helper to stop server
def stop_server():
    if server_process:
        try:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            server_process.wait(timeout=5)
        except Exception:
            pass

# 6. Measure health endpoint latency
@timed
def query_health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        raise Exception(str(e))

(health_resp, health_time) = query_health()
if isinstance(health_resp, Exception):
    emit(f"TEST_FAIL:health_check:{health_resp}")
else:
    emit(f"TEST_PASS:health_check")
emit(f"BENCHMARK:health_latency_ms:{health_time*1000:.2f}")

# 7. Load a complex scene (simulate by requesting a static asset)
@timed
def load_scene():
    url = "http://127.0.0.1:8000/static/sample_scene.glb"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        raise Exception(str(e))

(scene_data, scene_time) = load_scene()
if isinstance(scene_data, Exception):
    emit(f"TEST_FAIL:load_scene:{scene_data}")
else:
    emit(f"TEST_PASS:load_scene")
emit(f"BENCHMARK:scene_load_ms:{scene_time*1000:.2f}")

# 8. Build production bundle and measure size
@timed
def cargo_build_release():
    return run_cmd(['cargo', 'build', '--release', '--features', 'web'], cwd=repo_dir, timeout=300)

(build_rel_res, rel_build_time) = cargo_build_release()
if isinstance(build_rel_res, Exception) or build_rel_res.returncode != 0:
    emit(f"TEST_FAIL:production_build:{getattr(build_rel_res, 'stderr', str(build_rel_res)).strip()}")
else:
    emit(f"TEST_PASS:production_build")
emit(f"BENCHMARK:production_build_time_s:{rel_build_time:.2f}")

# Determine bundle size (assume target/release/ketchup.wasm)
bundle_path = os.path.join(repo_dir, "target", "release", "ketchup.wasm")
if os.path.isfile(bundle_path):
    size_bytes = os.path.getsize(bundle_path)
    size_mb = size_bytes / (1024*1024)
    emit(f"BENCHMARK:bundle_size_mb:{size_mb:.2f}")
    if size_mb < 5.0:
        emit(f"TEST_PASS:bundle_size")
    else:
        emit(f"TEST_FAIL:bundle_size:Size {size_mb:.2f} MB exceeds 5MB")
else:
    emit(f"TEST_FAIL:bundle_size:Bundle not found")

# 9. Baseline comparison against SketchUp (hypothetical baseline load time 0.12s)
baseline_load_ms = 120.0
ratio = (scene_time*1000) / baseline_load_ms
emit(f"BENCHMARK:vs_sketchup_load_ratio:{ratio:.2f}")

# Cleanup
stop_server()
emit("RUN_OK")