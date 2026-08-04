import subprocess
import pip
import time
import tracemalloc
import importlib

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'homebench'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError:
    # Fallback to git clone and pip install -e .
    subprocess.run(['git', 'clone', 'https://github.com/david-g-3654/homebench.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './homebench'], check=True, cwd='./homebench')
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Import homebench
try:
    import homebench
    import_time = time.time()
    tracemalloc.start()
    importlib.reload(homebench)
    import_time_ms = (time.time() - import_time) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:import_time_ms:{import_time_ms}')
    print(f'BENCHMARK:import_memory_mb:{current / 1024 / 1024}')
except Exception as e:
    print(f'TEST_fail:import.homebench:{str(e)}')

# Benchmark a local LLM with 1000 queries
try:
    import homebench
    start_time = time.time()
    tracemalloc.start()
    homebench.benchmark_local_llm(1000)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    benchmark_time_ms = (end_time - start_time) * 1000
    print(f'BENCHMARK:benchmark_time_ms:{benchmark_time_ms}')
    print(f'BENCHMARK:benchmark_memory_mb:{peak / 1024 / 1024}')
    print('TEST_PASS:benchmark_local_llm')
except Exception as e:
    print(f'TEST_fail:benchmark_local_llm:{str(e)}')

# Measure memory usage with 1000 queries
try:
    import homebench
    tracemalloc.start()
    start_time = time.time()
    homebench.measure_memory_usage(1000)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    measure_time_ms = (end_time - start_time) * 1000
    print(f'BENCHMARK:measure_time_ms:{measure_time_ms}')
    print(f'BENCHMARK:measure_memory_mb:{peak / 1024 / 1024}')
    print('TEST_PASS:measure_memory_usage')
except Exception as e:
    print(f'TEST_fail:measure_memory_usage:{str(e)}')

# Compare results to existing benchmarks
try:
    import homebench
    import llm_eval_harness
    start_time = time.time()
    homebench.benchmark_local_llm(1000)
    end_time = time.time()
    homebench_time_ms = (end_time - start_time) * 1000
    start_time = time.time()
    llm_eval_harness.benchmark_local_llm(1000)
    end_time = time.time()
    llm_eval_harness_time_ms = (end_time - start_time) * 1000
    ratio = homebench_time_ms / llm_eval_harness_time_ms
    print(f'BENCHMARK:vs_llm_eval_harness_ratio:{ratio}')
    print('TEST_PASS:compare_benchmarks')
except Exception as e:
    print(f'TEST_fail:compare_benchmarks:{str(e)}')

print('RUN_OK')