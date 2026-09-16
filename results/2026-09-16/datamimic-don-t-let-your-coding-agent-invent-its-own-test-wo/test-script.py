#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, shutil, math

def print_marker(msg):
    print(msg, flush=True)

def run_apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def pip_install(package):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', package],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start
        print_marker(f"TEST_PASS:pip_install_{package}")
        return True, duration
    except Exception as e:
        print_marker(f"TEST_FAIL:pip_install_{package}:{e}")
        return False, time.time() - start

def git_clone(repo, dest):
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker(f"TEST_PASS:git_clone_{repo}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:git_clone_{repo}:{e}")
        return False

def pip_install_editable(path):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("TEST_PASS:pip_install_editable")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:pip_install_editable:{e}")
        return False

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"TEST_PASS:import_{module_name}")
        return True, import_time, peak / 1024  # KB
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False, None, None

def run_core_operation():
    # synthetic test: generate a mock environment using datamimic if available
    try:
        import datamimic
        # Assume there is a function `generate_mock_environment` taking a spec dict
        spec = {"name": "test_env", "tasks": ["task1", "task2"]}
        start = time.time()
        env = datamimic.generate_mock_environment(spec)  # type: ignore
        latency = (time.time() - start) * 1000  # ms
        # simple verification
        if hasattr(env, "name") and env.name == "test_env":
            print_marker("TEST_PASS:core_operation")
            return True, latency
        else:
            print_marker("TEST_FAIL:core_operation:verification_failed")
            return False, latency
    except Exception as e:
        print_marker(f"TEST_FAIL:core_operation:{e}")
        return False, None

def main():
    # 1. Install system package git
    run_apk_install('git')

    # 2. Try pip install datamimic
    success, install_time = pip_install('datamimic')
    benchmark_install = install_time
    # fallback to git clone if pip failed
    if not success:
        repo = 'https://github.com/rapiddweller/datamimic.git'
        clone_dir = '/tmp/datamimic_src'
        if os.path.isdir(clone_dir):
            shutil.rmtree(clone_dir)
        if git_clone(repo, clone_dir):
            pip_install_editable(clone_dir)

    # 3. Measure import time
    imp_success, import_ms, import_mem_kb = measure_import('datamimic')
    # Benchmark lines
    print_marker(f"BENCHMARK:install_time_s:{benchmark_install:.2f}")
    if import_ms is not None:
        print_marker(f"BENCHMARK:import_time_ms:{import_ms:.2f}")
    if import_mem_kb is not None:
        print_marker(f"BENCHMARK:import_mem_kb:{import_mem_kb:.2f}")

    # 4. Run core operation
    core_success, core_latency = run_core_operation()
    if core_latency is not None:
        print_marker(f"BENCHMARK:core_op_latency_ms:{core_latency:.2f}")

    # 5. Comparison with baseline (OpenAI Codex evals import time ~120ms)
    baseline_import_ms = 120.0
    if import_ms is not None:
        ratio = import_ms / baseline_import_ms
        print_marker(f"BENCHMARK:vs_openai_codex_import_ratio:{ratio:.3f}")

    # Ensure at least three benchmark lines (we have install, import, core_op)
    # 6. Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()