import subprocess
import time
import tracemalloc
import importlib.util
import sys

def install_package(package_name):
    try:
        subprocess.run(['pip', 'install', package_name], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', f'https://github.com/woxi-project/{package_name}.git'], check=True)
            subprocess.run(['pip', 'install', '-e', '.'], cwd=package_name, check=True)
            print('INSTALL_OK')
        except subprocess.CalledProcessError as e:
            print(f'INSTALL_FAIL:{"pip install and git clone failed"}')

def test_import_time(package_name):
    try:
        start_time = time.time()
        importlib.import_module(package_name)
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
        print(f'TEST_PASS:import_time')
    except ImportError as e:
        print(f'TEST_FAIL:import_time:{e}')

def test_functional_test():
    try:
        start_time = time.time()
        import woxi
        woxi.evaluate('1+1')
        end_time = time.time()
        functional_test_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:functional_test_time_ms:{functional_test_time:.2f}')
        print(f'TEST_PASS:functional_test')
    except Exception as e:
        print(f'TEST_FAIL:functional_test:{e}')

def test_performance():
    try:
        start_time = time.time()
        import woxi
        for _ in range(1000):
            woxi.evaluate('1+1')
        end_time = time.time()
        performance_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:performance_time_ms:{performance_time:.2f}')
        print(f'TEST_PASS:performance_test')
    except Exception as e:
        print(f'TEST_FAIL:performance_test:{e}')

def test_wolfram_language_compatibility():
    try:
        import woxi
        woxi.evaluate('N[Pi, 10]')
        print(f'TEST_PASS:wolfram_language_compatibility')
    except Exception as e:
        print(f'TEST_FAIL:wolfram_language_compatibility:{e}')

def compare_to_baseline():
    try:
        import woxi
        start_time = time.time()
        for _ in range(1000):
            woxi.evaluate('1+1')
        end_time = time.time()
        woxi_time = (end_time - start_time) * 1000

        import numpy as np
        start_time = time.time()
        for _ in range(1000):
            np.add(1, 1)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000

        ratio = woxi_time / baseline_time
        print(f'BENCHMARK:vs_numpy_add_ratio:{ratio:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:compare_to_baseline:{e}')

def test_memory_usage():
    try:
        tracemalloc.start()
        import woxi
        woxi.evaluate('1+1')
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_bytes:{peak}')
        tracemalloc.stop()
        print(f'TEST_PASS:memory_usage')
    except Exception as e:
        print(f'TEST_FAIL:memory_usage:{e}')

def test_loc_count():
    try:
        import os
        loc_count = 0
        for root, dirs, files in os.walk('woxi'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        lines = f.readlines()
                        loc_count += len(lines)
        print(f'BENCHMARK:loc_count:{loc_count}')
        print(f'TEST_PASS:loc_count')
    except Exception as e:
        print(f'TEST_FAIL:loc_count:{e}')

def test_test_files_count():
    try:
        import os
        test_files_count = 0
        for root, dirs, files in os.walk('woxi'):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files_count += 1
        print(f'BENCHMARK:test_files_count:{test_files_count}')
        print(f'TEST_PASS:test_files_count')
    except Exception as e:
        print(f'TEST_FAIL:test_files_count:{e}')

def main():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    install_package('woxi')
    test_import_time('woxi')
    test_functional_test()
    test_performance()
    test_wolfram_language_compatibility()
    compare_to_baseline()
    test_memory_usage()
    test_loc_count()
    test_test_files_count()
    print('RUN_OK')

if __name__ == '__main__':
    main()