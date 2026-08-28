import subprocess, sys, time, tracemalloc, os, json, math, traceback

def print_marker(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk_packages():
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache', 'git'])
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print_marker(f"INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else str(e)).replace('\n', ' ')
        print_marker(f"INSTALL_FAIL:{reason}")
    print_marker(f"BENCHMARK:apk_git_install_time_s:{elapsed:.3f}")

def pip_install_package():
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'OpenTIE'])
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        # fallback to git clone + editable install
        fallback_start = time.time()
        clone_dir = "/tmp/opentie_src"
        if os.path.isdir(clone_dir):
            subprocess.run(['rm', '-rf', clone_dir])
        res_clone = run_cmd(['git', 'clone', 'https://github.com/elyosh/OpenTIE', clone_dir])
        if res_clone and res_clone.returncode == 0:
            res_edit = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', clone_dir])
            if res_edit and res_edit.returncode == 0:
                print_marker("INSTALL_OK")
            else:
                reason = (res_edit.stderr.strip() if res_edit else "editable install failed")
                print_marker(f"INSTALL_FAIL:{reason}")
        else:
            reason = (res_clone.stderr.strip() if res_clone else "git clone failed")
            print_marker(f"INSTALL_FAIL:{reason}")
        elapsed = time.time() - fallback_start
    print_marker(f"BENCHMARK:pip_install_time_s:{elapsed:.3f}")

def benchmark_import():
    start = time.time()
    tracemalloc.start()
    try:
        import OpenTIE
        import_time = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"TEST_PASS:import_module")
        print_marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
        print_marker(f"BENCHMARK:import_peak_mem_kb:{peak/1024:.2f}")
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_module:{e}")
        print_marker(f"BENCHMARK:import_time_ms:0")
        print_marker(f"BENCHMARK:import_peak_mem_kb:0")

def minimal_functional_test():
    start = time.time()
    try:
        # Assuming the package provides a function to initialize the engine or similar.
        # Use getattr to avoid AttributeError if not present.
        init_func = getattr(OpenTIE, 'initialize', None)
        if callable(init_func):
            init_func()
            duration = time.time() - start
            print_marker(f"TEST_PASS:initialize")
        else:
            # Fallback: call a dummy method if exists
            dummy = getattr(OpenTIE, 'run', None)
            if callable(dummy):
                dummy()
                duration = time.time() - start
                print_marker(f"TEST_PASS:run")
            else:
                raise AttributeError("No known entry point in OpenTIE")
        print_marker(f"BENCHMARK:core_op_latency_ms:{duration*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:core_operation:{e}")
        print_marker(f"BENCHMARK:core_op_latency_ms:0")

def compare_with_baseline():
    # Baseline: XWA (assume import time ~120ms, core op ~200ms)
    baseline_import = 0.120
    baseline_core = 0.200
    # Use last measured values from environment variables if set, otherwise dummy.
    try:
        import_time = float(next(line for line in open(os.getenv('PYTHONPATH','/dev/null')) if line.startswith('BENCHMARK:import_time_ms')).split(":")[2])
    except Exception:
        import_time = 0.0
    # For ratio calculations use measured import_time_ms if available
    if import_time > 0:
        ratio = (import_time/1000) / baseline_import
        print_marker(f"BENCHMARK:vs_xwa_import_ratio:{ratio:.2f}")
    # core op ratio
    try:
        core_time = float(next(line for line in open(os.getenv('PYTHONPATH','/dev/null')) if line.startswith('BENCHMARK:core_op_latency_ms')).split(":")[2])
    except Exception:
        core_time = 0.0
    if core_time > 0:
        ratio_core = (core_time/1000) / baseline_core
        print_marker(f"BENCHMARK:vs_xwa_core_ratio:{ratio_core:.2f}")

def main():
    try:
        install_apk_packages()
    except Exception as e:
        print_marker(f"TEST_FAIL:apk_install:{e}")

    try:
        pip_install_package()
    except Exception as e:
        print_marker(f"TEST_FAIL:pip_install:{e}")

    try:
        benchmark_import()
    except Exception as e:
        print_marker(f"TEST_FAIL:benchmark_import:{e}")

    try:
        minimal_functional_test()
    except Exception as e:
        print_marker(f"TEST_FAIL:minimal_functional_test:{e}")

    try:
        compare_with_baseline()
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_baseline:{e}")

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()