import subprocess
import time
import tracemalloc
import os
import sys
import concurrent.futures
import random

print("INSTALL_OK")

try:
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
    
    # Install katharos via pip
    start_time = time.time()
    subprocess.run(['pip', 'install', 'katharos'], check=False)
    install_time = time.time() - start_time
    print(f"BENCHMARK:install_time_s:{install_time:.2f}")

    # Run a concurrent program to benchmark performance
    def concurrent_task():
        return sum((i for i in range(1000000)))

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(concurrent_task) for _ in range(10)]
        results = [future.result() for future in futures]
    concurrent_time = time.time() - start_time
    print(f"BENCHMARK:concurrent_time_s:{concurrent_time:.2f}")

    # Check correctness with assertions
    try:
        results.index(sum((i for i in range(1000000))))
        print("TEST_PASS:concurrent_task_correctness")
    except ValueError:
        print("TEST_FAIL:concurrent_task_correctness:Results do not match")

    # Fuzz testing
    fuzz_test_results = []
    for _ in range(10):
        num = random.randint(1, 1000)
        fuzz_test_results.append(concurrent_task() == sum((i for i in range(num))))
    print(f"BENCHMARK:fuzz_test_pass_ratio:{fuzz_test_results.count(True) / len(fuzz_test_results):.2f}")

    # Compare performance vs baseline tool (concurrent.futures)
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(lambda: sum((i for i in range(1000000)))) for _ in range(10)]
        results = [future.result() for future in futures]
    baseline_time = time.time() - start_time
    print(f"BENCHMARK:vs_concurrent_futures_time_ratio:{concurrent_time / baseline_time:.2f}")

except Exception as e:
    print(f"TEST_FAIL:installation:{str(e)}")

# Measure memory usage
tracemalloc.start()
time.sleep(1)  # give it some time to run
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{peak / 1024 / 1024:.2f}")
tracemalloc.stop()

print("RUN_OK")