import os
import sys
import subprocess
import time
import traceback
import importlib.util
import tracemalloc

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=True, text=True, **kwargs)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)

def bench(name, value):
    marker(f"BENCHMARK:{name}:{value}")

def test_skip(name, reason):
    marker(f"TEST_SKIP:{name}:{reason}")

def test_fail(name, reason):
    marker(f"TEST_FAIL:{name}:{reason}")

def test_pass(name):
    marker(f"TEST_PASS:{name}")

# 1. Install system package git
start = time.time()
ok, err = run_cmd(['apk', 'add', '--no-cache', 'git'])
if ok:
    marker("INSTALL_OK")
else:
    marker(f"INSTALL_FAIL:{err}")
install_time = time.time() - start
bench("install_time_s", f"{install_time:.3f}")

# 2. Clone repository
repo_url = "https://github.com/pantel/ai-gaming-companion"
repo_dir = "/tmp/ai-gaming-companion"
if os.path.isdir(repo_dir):
    subprocess.run(['rm', '-rf', repo_dir])
start = time.time()
try:
    subprocess.run(['git', 'clone', '--depth', '1', repo_url, repo_dir],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    test_pass("clone_repo")
except Exception as e:
    test_fail("clone_repo", str(e))
clone_time = time.time() - start
bench("clone_time_s", f"{clone_time:.3f}")

# 3. Install Python dependencies
os.chdir(repo_dir)
start = time.time()
install_success = False
install_err = ""
# first try requirements.txt
req_path = os.path.join(repo_dir, "requirements.txt")
if os.path.isfile(req_path):
    ok, err = run_cmd([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ok:
        install_success = True
    else:
        install_err = err

# fallback to editable install
if not install_success:
    ok, err = run_cmd([sys.executable, "-m", "pip", "install", "-e", "."],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ok:
        install_success = True
    else:
        install_err = err

if install_success:
    test_pass("install_deps")
else:
    test_fail("install_deps", install_err)
bench("install_deps_time_s", f"{time.time() - start:.3f}")

# 4. Import the package and measure import time
import_start = time.time()
try:
    spec = importlib.util.find_spec("ai_gaming_companion")
    if spec is None:
        raise ImportError("module not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    test_pass("import_module")
except Exception as e:
    test_fail("import_module", str(e))
import_time = (time.time() - import_start) * 1000  # ms
bench("import_time_ms", f"{import_time:.2f}")

# 5. Run minimal functional test
# Assume the package provides a class Companion with method handle_event(event_dict)
bench_start = time.time()
tracemalloc.start()
try:
    # Try to instantiate companion in headless mode
    if hasattr(module, "Companion"):
        companion = module.Companion(headless=True)
        test_pass("instantiate_companion")
    else:
        raise AttributeError("Companion class not found")
except Exception as e:
    test_fail("instantiate_companion", str(e))
    companion = None

# 6. Send mock event and verify response
if companion:
    try:
        mock_event = {"type": "dialog", "text": "Hello there!"}
        resp_start = time.time()
        response = companion.handle_event(mock_event)
        resp_latency = (time.time() - resp_start) * 1000  # ms
        if response:
            test_pass("mock_event_response")
        else:
            test_fail("mock_event_response", "empty response")
        bench("event_latency_ms", f"{resp_latency:.2f}")
    except Exception as e:
        test_fail("mock_event_response", traceback.format_exc())
else:
    test_skip("mock_event_response", "companion not instantiated")

# 7. Ensure latency < 100ms
if 'resp_latency' in locals():
    if resp_latency < 100:
        test_pass("latency_requirement")
    else:
        test_fail("latency_requirement", f"{resp_latency:.2f}ms > 100ms")
else:
    test_skip("latency_requirement", "latency not measured")

# 8. Memory usage benchmark
current, peak = tracemalloc.get_traced_memory()
bench("memory_peak_kb", f"{peak/1024:.2f}")
tracemalloc.stop()

# 9. Baseline comparison with LangChain (assume baseline latency 120ms)
baseline_latency = 120.0
if 'resp_latency' in locals():
    ratio = resp_latency / baseline_latency
    bench(f"vs_langchain_latency_ratio", f"{ratio:.3f}")

# Final marker
marker("RUN_OK")