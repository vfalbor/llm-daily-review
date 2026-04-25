import subprocess
import time
import tracemalloc
import importlib.util
import pip
import sys
import os

def install_dependencies():
    try:
        # installing necessary dependencies
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        # installing pip packages
        pip.main(['install', 'lambdpy'])
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def run_benchmark():
    try:
        start_import_time = time.time()
        # loading the library
        spec = importlib.util.find_spec('lambdpy')
        if spec is None:
            print(f'TEST_FAIL:lambdpy_import:Module not found')
            return
        start_import_time_after_load = time.time()
        import lambdpy
        end_import_time = time.time()

        # running a simple benchmark
        start_benchmark_time = time.time()
        lambdpy.main()
        end_benchmark_time = time.time()

        # calculating benchmark metrics
        import_time = (end_import_time - start_import_time) * 1000
        import_time_after_load = (end_import_time - start_import_time_after_load) * 1000
        benchmark_time = (end_benchmark_time - start_benchmark_time) * 1000

        print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
        print(f'BENCHMARK:import_time_after_load_ms:{import_time_after_load:.2f}')
        print(f'BENCHMARK:benchmark_time_ms:{benchmark_time:.2f}')

        # running the same benchmark with Python for baseline comparison
        start_baseline_time = time.time()
        # simple Python lambda function
        f = lambda x: x**2
        for _ in range(10000):
            f(5)
        end_baseline_time = time.time()

        # calculating baseline metrics
        baseline_time = (end_baseline_time - start_baseline_time) * 1000
        ratio = import_time / baseline_time

        print(f'BENCHMARK:vs_python_import_ratio:{ratio:.2f}')
        print(f'BENCHMARK:vs_python_benchmark_ratio:{benchmark_time / baseline_time:.2f}')

        print('TEST_PASS:lambdpy_benchmark')

    except Exception as e:
        print(f'TEST_FAIL:lambdpy_benchmark:{str(e)}')

    try:
        # measuring memory usage
        tracemalloc.start()
        import lambdpy
        lambdpy.main()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:peak_memory_usage:{peak / 1024:.2f} KB')

        # measuring lines of code
        with open(__file__, 'r') as f:
            lines = len(f.readlines())
        print(f'BENCHMARK:loc_count:{lines}')

    except Exception as e:
        print(f'TEST_FAIL:memory_benchmark:{str(e)}')

def main():
    install_dependencies()
    run_benchmark()
    print('RUN_OK')

if __name__ == '__main__':
    main()