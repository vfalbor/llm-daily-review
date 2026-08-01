import subprocess
import time
import tracemalloc
import importlib.util
import sys

def install_package(package_name):
    try:
        subprocess.run(['pip', 'install', package_name], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', f'https://github.com/{package_name}.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './bigfood'], check=True)
            print("INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL: {e}")

def test_install_and_basic_run(package_name):
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is not None:
            package = importlib.import_module(package_name)
            package.main()
            print(f"TEST_PASS:{package_name}_basic_run")
        else:
            print(f"TEST_FAIL:{package_name}_basic_run:package not found")
    except Exception as e:
        print(f"TEST_FAIL:{package_name}_basic_run: {e}")

def test_performance(package_name):
    try:
        start_time = time.time()
        package = importlib.import_module(package_name)
        package.main()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:basic_operation_latency_ms:{latency}")
        tracemalloc.start()
        package.main()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        print(f"TEST_PASS:{package_name}_performance")
    except Exception as e:
        print(f"TEST_FAIL:{package_name}_performance: {e}")

def compare_with_baseline(package_name):
    try:
        import random
        import time
        start_time = time.time()
        importlib.import_module('random')
        end_time = time.time()
        python_import_time = (end_time - start_time) * 1000
        start_time = time.time()
        importlib.import_module(package_name)
        end_time = time.time()
        package_import_time = (end_time - start_time) * 1000
        ratio = package_import_time / python_import_time
        print(f"BENCHMARK:vs_python_import_time_ratio:{ratio}")
        print(f"TEST_PASS:{package_name}_compare_with_baseline")
    except Exception as e:
        print(f"TEST_FAIL:{package_name}_compare_with_baseline: {e}")

if __name__ == '__main__':
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    package_name = 'bigfood'
    install_package(package_name)
    test_install_and_basic_run(package_name)
    test_performance(package_name)
    compare_with_baseline(package_name)
    print("RUN_OK")