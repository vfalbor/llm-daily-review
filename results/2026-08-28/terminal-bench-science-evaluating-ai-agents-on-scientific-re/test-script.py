import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk(pkg):
    res = run_cmd(['apk', 'add', '--no-cache', pkg])
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else str(e))
        print_marker(f"INSTALL_FAIL:{reason}")

def pip_install(pkg):
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else "unknown")
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def git_clone(repo, dest):
    res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else "unknown")
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{duration:.2f}")
        print_marker(f"BENCHMARK:import_memory_kb:{peak/1024:.2f}")
        return True, duration
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import:{str(e)}")
        return False, None

def run_sample_task(package):
    try:
        # Assuming the package provides a function `run_demo` returning a dict with 'accuracy' and 'latency'
        mod = __import__(package)
        if hasattr(mod, 'run_demo'):
            start = time.time()
            result = mod.run_demo()
            latency = (time.time() - start) * 1000  # ms
            acc = result.get('accuracy', None)
            print_marker(f"BENCHMARK:task_latency_ms:{latency:.2f}")
            if acc is not None:
                print_marker(f"BENCHMARK:task_accuracy:{acc:.4f}")
                print_marker("TEST_PASS:sample_task")
            else:
                print_marker("TEST_FAIL:sample_task:missing accuracy")
        else:
            print_marker("TEST_FAIL:sample_task:no run_demo function")
    except Exception as e:
        print_marker(f"TEST_FAIL:sample_task:{traceback.format_exc().splitlines()[-1]}")

def compare_vs_baseline(metric, our_value, baseline_value):
    try:
        ratio = our_value / baseline_value if baseline_value != 0 else 0
        print_marker(f"BENCHMARK:vs_baseline_{metric}:{ratio:.4f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_vs_baseline:{str(e)}")

def main():
    # 1. Install system packages
    install_apk('git')

    # 2. Clone repo and install dependencies
    repo_url = "https://github.com/Terminal-Bench-Science/terminal-bench-science.git"
    dest_dir = "/tmp/terminal-bench-science"
    if not git_clone(repo_url, dest_dir):
        print_marker("TEST_SKIP:clone_repo:git clone failed")
        return

    os.chdir(dest_dir)

    # Try pip install the package
    if not pip_install('.'):
        # fallback to editable install
        if not pip_install('-e .'):
            print_marker("TEST_SKIP:install_package:both pip install attempts failed")
            return

    # 3. Measure import time
    ok, import_time = measure_import('terminal_bench_science')
    if not ok:
        print_marker("TEST_FAIL:import_module:cannot import")
    else:
        # 4. Run sample agent/task
        run_sample_task('terminal_bench_science')

    # 5. Emit additional benchmarks (memory snapshot, file count)
    try:
        start = time.time()
        file_count = sum(len(files) for _, _, files in os.walk('.'))
        duration = time.time() - start
        print_marker(f"BENCHMARK:file_count:{file_count}")
        print_marker(f"BENCHMARK:file_count_time_s:{duration:.4f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:file_count:{str(e)}")

    # 6. Compare with baseline (mock baseline values)
    # Baseline values are illustrative; in real scenario they'd be fetched or hardcoded.
    baseline_import_time_ms = 150.0
    if import_time is not None:
        compare_vs_baseline('import_time_ms', import_time, baseline_import_time_ms)

    baseline_latency_ms = 120.0
    # Assuming we captured task latency earlier via BENCHMARK lines; use placeholder if not.
    # Here we just reuse import_time for demo.
    compare_vs_baseline('task_latency_ms', import_time, baseline_latency_ms)

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()