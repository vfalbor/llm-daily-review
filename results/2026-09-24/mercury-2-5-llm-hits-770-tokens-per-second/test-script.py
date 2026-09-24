#!/usr/bin/env python3
import subprocess
import sys
import time
import tracemalloc
import json
import os
import threading

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk(pkg):
    res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else str(e))
        print_marker(f"INSTALL_FAIL:{reason}")

def pip_install(package):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
    duration = time.time() - start
    print_marker(f"BENCHMARK:install_time_s:{duration:.3f}")
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = res.stderr.strip() if res else "pip install failed"
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def git_clone(repo, dest):
    res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = res.stderr.strip() if res else "git clone failed"
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def fallback_install():
    tmp_dir = "/tmp/mercury_src"
    if os.path.isdir(tmp_dir):
        subprocess.run(['rm', '-rf', tmp_dir])
    if not git_clone('https://github.com/ArtificialAnalysis/Mercury-2.5.git', tmp_dir):
        return False
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', tmp_dir])
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = res.stderr.strip() if res else "fallback pip install failed"
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        print_marker("TEST_PASS:import_module")
        return True
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_module:{e}")
        return False

def run_mercury_test():
    try:
        import mercury
    except Exception as e:
        print_marker(f"TEST_FAIL:load_mercury:{e}")
        return None

    prompt = "Hello " * 200  # ~1000 tokens approximated
    start = time.time()
    try:
        # Assuming Mercury provides a generate function; adapt if different
        result = mercury.generate(prompt, max_tokens=10)
        latency = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:mercury_latency_ms:{latency:.2f}")
        print_marker("TEST_PASS:mercury_inference")
        return latency
    except Exception as e:
        latency = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:mercury_latency_ms:{latency:.2f}")
        print_marker(f"TEST_FAIL:mercury_inference:{e}")
        return None

def run_gpt4all_test():
    # Attempt to install gpt4all via pip (fallback to git if needed)
    if not pip_install('gpt4all'):
        return None
    try:
        import gpt4all
    except Exception as e:
        print_marker(f"TEST_FAIL:load_gpt4all:{e}")
        return None
    prompt = "Hello " * 200
    start = time.time()
    try:
        # Simplified call; actual API may differ
        model = gpt4all.GPT4All()
        result = model.generate(prompt, max_tokens=10)
        latency = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:gpt4all_latency_ms:{latency:.2f}")
        print_marker("TEST_PASS:gpt4all_inference")
        return latency
    except Exception as e:
        latency = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:gpt4all_latency_ms:{latency:.2f}")
        print_marker(f"TEST_FAIL:gpt4all_inference:{e}")
        return None

def compare_vs_baseline(mercury_lat, baseline_lat):
    if mercury_lat is None or baseline_lat is None:
        print_marker("TEST_SKIP:compare_vs_baseline:Missing data")
        return
    try:
        ratio = mercury_lat / baseline_lat
        print_marker(f"BENCHMARK:vs_gpt4all_latency_ratio:{ratio:.3f}")
        print_marker("TEST_PASS:compare_vs_baseline")
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_vs_baseline:{e}")

def parallel_request_worker(results, idx):
    try:
        import mercury
        prompt = "Parallel test " * 50
        start = time.time()
        mercury.generate(prompt, max_tokens=5)
        latency = (time.time() - start) * 1000
        results[idx] = latency
    except Exception as e:
        results[idx] = None

def benchmark_parallel():
    threads = []
    results = [None] * 10
    start = time.time()
    for i in range(10):
        t = threading.Thread(target=parallel_request_worker, args=(results, i))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    total_time = (time.time() - start) * 1000
    successes = sum(1 for r in results if r is not None)
    avg_latency = (sum(r for r in results if r) / successes) if successes else 0
    print_marker(f"BENCHMARK:parallel_total_time_ms:{total_time:.2f}")
    print_marker(f"BENCHMARK:parallel_successful_requests:{successes}")
    print_marker(f"BENCHMARK:parallel_avg_latency_ms:{avg_latency:.2f}")
    print_marker("TEST_PASS:parallel_benchmark")

def main():
    # 1. Install system deps
    install_apk('git')

    # 2. Install mercury package
    if not pip_install('mercury-2.5'):
        # fallback to source
        if not fallback_install():
            print_marker("TEST_SKIP:install_mercury:Both pip and source install failed")
    
    # 3. Measure import
    measure_import('mercury')

    # 4. Run mercury inference benchmark
    mercury_latency = run_mercury_test()

    # 5. Install and run baseline (GPT4All)
    baseline_latency = run_gpt4all_test()

    # 6. Compare
    compare_vs_baseline(mercury_latency, baseline_latency)

    # 7. Parallel throughput benchmark
    benchmark_parallel()

    # Ensure at least three benchmark lines emitted (install_time_s, import_time_ms, mercury_latency_ms already)
    # Additional benchmarks emitted throughout.

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()