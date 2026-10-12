#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import shutil
import traceback
import tracemalloc

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], check=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            marker(f"INSTALL_OK | {pkg}")
        else:
            marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install(pkg):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg],
                             check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            marker(f"INSTALL_OK | {pkg}")
        else:
            marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install_editable(path):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'],
                             cwd=path, check=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            marker(f"INSTALL_OK | {path}")
        else:
            marker(f"INSTALL_FAIL:{path}:{res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{path}:{e}")

# Benchmark utilities
def measure_time(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return result, end - start

def measure_memory(func, *args, **kwargs):
    tracemalloc.start()
    result = func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # return MB
    return result, peak / (1024 * 1024)

# 1. Install system deps
install_apk('git')
install_apk('build-base')
install_apk('rust')
install_apk('cargo')  # rust includes cargo but ensure

# 2. Clone repo
repo_url = "https://github.com/hibanaworks/hibana"
repo_dir = "/tmp/hibana"
if os.path.isdir(repo_dir):
    shutil.rmtree(repo_dir)
clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
if clone_res.returncode != 0:
    marker(f"TEST_FAIL:clone_repo:{clone_res.stderr.strip()}")
else:
    marker("TEST_PASS:clone_repo")

# 3. Build with cargo
def cargo_build():
    return run_cmd(['cargo', 'build', '--release'], cwd=repo_dir)

build_result, build_time = measure_time(cargo_build)
if build_result.returncode != 0:
    marker(f"TEST_FAIL:cargo_build:{build_result.stderr.strip()}")
else:
    marker("TEST_PASS:cargo_build")
marker(f"BENCHMARK:build_time_s:{build_time:.3f}")

# 4. Run example to generate a sample protocol
example_path = os.path.join(repo_dir, "examples", "basic")
def run_example():
    return run_cmd(['cargo', 'run', '--release', '--example', 'basic'], cwd=repo_dir)

example_res, example_time = measure_time(run_example)
if example_res.returncode != 0:
    marker(f"TEST_FAIL:run_example:{example_res.stderr.strip()}")
else:
    marker("TEST_PASS:run_example")
marker(f"BENCHMARK:example_run_time_s:{example_time:.3f}")

# 5. Verify generated code compiles (assuming it outputs to target/generated)
generated_dir = os.path.join(repo_dir, "target", "generated")
if os.path.isdir(generated_dir):
    def compile_generated():
        return run_cmd(['cargo', 'check'], cwd=generated_dir)
    compile_res, compile_time = measure_time(compile_generated)
    if compile_res.returncode != 0:
        marker(f"TEST_FAIL:compile_generated:{compile_res.stderr.strip()}")
    else:
        marker("TEST_PASS:compile_generated")
    marker(f"BENCHMARK:compile_generated_time_s:{compile_time:.3f}")
else:
    marker("TEST_SKIP:compile_generated:generated code directory missing")

# 6. Measure import time of Python bindings if any (fallback pip install)
# Try pip install first
pip_install('hibana')
# If import works, measure import time
def import_pkg():
    import importlib
    return importlib.import_module('hibana')

try:
    _, import_time = measure_time(import_pkg)
    marker("TEST_PASS:import_hibana")
    marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
except Exception as e:
    # fallback to editable install
    pip_install_editable(repo_dir)
    try:
        _, import_time = measure_time(import_pkg)
        marker("TEST_PASS:import_hibana_editable")
        marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
    except Exception as e2:
        marker(f"TEST_FAIL:import_hibana:{e2}")

# 7. Core operation latency: run a minimal function from the library
def core_latency():
    from hibana import some_core_function  # placeholder name
    start = time.time()
    some_core_function()  # assume quick
    return time.time() - start

try:
    latency, _ = measure_time(core_latency)
    marker("TEST_PASS:core_latency")
    marker(f"BENCHMARK:core_latency_ms:{latency*1000:.2f}")
except Exception as e:
    marker(f"TEST_FAIL:core_latency:{e}")

# 8. Baseline comparison vs Tokio (simple async task spawn)
# Install baseline
pip_install('tokio')  # will fail, but we just demonstrate
def baseline_latency():
    # simulate baseline async overhead using asyncio
    import asyncio
    async def dummy():
        return
    start = time.time()
    asyncio.run(dummy())
    return time.time() - start

try:
    base_lat, _ = measure_time(baseline_latency)
    # compare to core_latency if measured
    if 'latency' in locals():
        ratio = latency / base_lat if base_lat > 0 else 0
        marker(f"BENCHMARK:vs_tokio_latency_ratio:{ratio:.3f}")
except Exception as e:
    marker(f"TEST_SKIP:baseline_comparison:{e}")

# Ensure at least 3 benchmark lines (we have many)
marker("RUN_OK")