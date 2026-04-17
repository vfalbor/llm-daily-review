import subprocess
import time
import tracemalloc
import importlib.util
import os

def install_packages():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    try:
        subprocess.run(['pip', 'install', 'pypyr'], check=True)
    except subprocess.CalledProcessError:
        subprocess.run(['git', 'clone', 'https://github.com/pypyr/pypyr.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './pypyr'], check=True)
    print('INSTALL_OK')

def compile_and_run():
    try:
        import pypyr
        start_time = time.time()
        pypyr.main(['-c', 'print("Hello, world!")'])
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:compile_time_ms:{latency}')
        print(f'TEST_PASS:compile_and_run')
    except Exception as e:
        print(f'TEST_FAIL:compile_and_run:{str(e)}')

def benchmark_execution_speed():
    try:
        import pypyr
        start_time = time.time()
        for _ in range(1000):
            pypyr.main(['-c', '1 + 1'])
        end_time = time.time()
        execution_time = end_time - start_time
        print(f'BENCHMARK:execution_speed_s:{execution_time}')
        print(f'TEST_PASS:benchmark_execution_speed')
    except Exception as e:
        print(f'TEST_FAIL:benchmark_execution_speed:{str(e)}')

def compare_memory_usage():
    try:
        import tracemalloc
        import pypyr
        tracemalloc.start()
        pypyr.main(['-c', 'print("Hello, world!")'])
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_peak_mb:{peak / 1024 / 1024}')
        print(f'TEST_PASS:compare_memory_usage')
    except Exception as e:
        print(f'TEST_FAIL:compare_memory_usage:{str(e)}')

def compare_performance_vs_baseline():
    try:
        import timeit
        import pypyr
        start_time = timeit.default_timer()
        for _ in range(100):
            pypyr.main(['-c', '1 + 1'])
        end_time = timeit.default_timer()
        pypyr_time = end_time - start_time
        start_time = timeit.default_timer()
        for _ in range(100):
            exec('1 + 1')
        end_time = timeit.default_timer()
        cpython_time = end_time - start_time
        ratio = pypyr_time / cpython_time
        print(f'BENCHMARK:vs_cpython_execution_ratio:{ratio}')
        print(f'TEST_PASS:compare_performance_vs_baseline')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance_vs_baseline:{str(e)}')

def main():
    install_packages()
    compile_and_run()
    benchmark_execution_speed()
    compare_memory_usage()
    compare_performance_vs_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()