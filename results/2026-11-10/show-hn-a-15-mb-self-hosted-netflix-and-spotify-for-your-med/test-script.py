#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, shutil, urllib.request
from pathlib import Path

def print_marker(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg])
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} exit {res.returncode}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} {e}")

def pip_install(pkg):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:pip {pkg} exit {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip {pkg} {e}")
        return False

def git_clone(url, dest):
    try:
        res = run_cmd(['git', 'clone', '--depth', '1', url, str(dest)])
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:git clone exit {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git clone {e}")
        return False

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        elapsed_ms = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:import_time_ms:{elapsed_ms:.2f}")
        print_marker(f"BENCHMARK:import_memory_kb:{peak/1024:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False
    finally:
        tracemalloc.stop()

def start_server_and_check(port=3000, timeout=10):
    try:
        # assume npm start runs in background; we start it and poll
        proc = subprocess.Popen(['npm', 'start'], cwd=str(repo_path), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start = time.time()
        while time.time() - start < timeout:
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}', timeout=1) as resp:
                    if resp.status == 200:
                        proc.terminate()
                        print_marker("TEST_PASS:start_server")
                        return True
            except:
                time.sleep(0.5)
        proc.terminate()
        print_marker("TEST_FAIL:start_server:timeout")
        return False
    except Exception as e:
        print_marker(f"TEST_FAIL:start_server:{e}")
        return False

def benchmark_vs_baseline(metric, value, baseline_value):
    try:
        ratio = value / baseline_value if baseline_value else 0
        print_marker(f"BENCHMARK:vs_{baseline}_{metric}:{ratio:.4f}")
    except Exception:
        pass

# -------------------- Main execution --------------------
install_apk('git')
install_apk('npm')  # npm is provided by nodejs package on Alpine
install_apk('nodejs')  # ensure node/npm available

repo_url = "https://github.com/HolyArrs/HolyArrs.git"
repo_path = Path("/tmp/HolyArrs")
if repo_path.exists():
    shutil.rmtree(repo_path)

# 1. Clone repo
if not git_clone(repo_url, repo_path):
    print_marker("TEST_FAIL:clone_repo:cannot clone")
else:
    print_marker("TEST_PASS:clone_repo")

# 2. npm install
npm_install_ok = False
try:
    res = run_cmd(['npm', 'install'], cwd=str(repo_path))
    if res.returncode == 0:
        npm_install_ok = True
        print_marker("TEST_PASS:npm_install")
    else:
        print_marker(f"TEST_FAIL:npm_install:exit {res.returncode}")
except Exception as e:
    print_marker(f"TEST_FAIL:npm_install:{e}")

# 3. Start server and verify UI
if npm_install_ok:
    start_server_and_check()
else:
    print_marker("TEST_SKIP:start_server:npm install failed")

# 4. Measure import time of package (fallback pip install if needed)
pkg_name = "HolyArrs"
installed = pip_install(pkg_name)
if not installed:
    # fallback: pip install from cloned repo
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=str(repo_path))
        installed = res.returncode == 0
        if installed:
            print_marker("TEST_PASS:pip_install_editable")
        else:
            print_marker("TEST_FAIL:pip_install_editable")
    except Exception as e:
        print_marker(f"TEST_FAIL:pip_install_editable:{e}")

if installed:
    measure_import(pkg_name)
else:
    print_marker("TEST_SKIP:import_pkg:install failed")

# Benchmark baseline comparison (using Jellyfin as example baseline)
# Dummy baseline values for demonstration
baseline_import_ms = 150.0
baseline_memory_kb = 5000.0

# Collect our own import metrics from previous markers (simple re-run)
start = time.time()
tracemalloc.start()
try:
    __import__(pkg_name)
    imp_elapsed = (time.time() - start) * 1000
    _, imp_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:import_time_ms:{imp_elapsed:.2f}")
    print_marker(f"BENCHMARK:import_memory_kb:{imp_peak/1024:.2f}")
    benchmark_vs_baseline("import_time_ms", imp_elapsed, baseline_import_ms)
    benchmark_vs_baseline("import_memory_kb", imp_peak/1024, baseline_memory_kb)
except Exception:
    tracemalloc.stop()

# Additional arbitrary benchmarks
file_count = sum(1 for _ in repo_path.rglob('*') if _.is_file())
print_marker(f"BENCHMARK:repo_file_count:{file_count}")

process = subprocess.run(['du', '-s', str(repo_path)], capture_output=True, text=True)
if process.returncode == 0:
    size_kb = int(process.stdout.split()[0])
    print_marker(f"BENCHMARK:repo_size_kb:{size_kb}")

# final marker
print_marker("RUN_OK")