import subprocess
import time
import tracemalloc
import importlib.util
import random

def install_boringbar():
    try:
        # Install system packages
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        # Clone the repo
        subprocess.run(['git', 'clone', 'https://github.com/boringbar/boringbar.git'], check=True)
        # Install pip dependencies
        subprocess.run(['pip', 'install', '-e', './boringbar'], cwd='./boringbar', check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_basic_run():
    try:
        import boringbar
        # Create synthetic data
        data = [random.randint(0, 100) for _ in range(100)]
        # Run a minimal functional test
        boringbar.run(data)
        print('TEST_PASS:test_basic_run')
    except Exception as e:
        print(f'TEST_FAIL:test_basic_run:{str(e)}')

def test_performance():
    try:
        import boringbar
        # Create synthetic data
        data = [random.randint(0, 100) for _ in range(1000)]
        start_time = time.time()
        boringbar.run(data)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:boringbar_latency_ms:{latency}')
    except Exception as e:
        print(f'TEST_FAIL:test_performance:{str(e)}')

def compare_performance():
    try:
        import boringbar
        # Create synthetic data
        data = [random.randint(0, 100) for _ in range(1000)]
        # Measure import time
        start_time = time.time()
        import boringbar
        import psutil
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        # Measure core operation latency
        start_time = time.time()
        boringbar.run(data)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        # Compare vs similar tool (e.g. python)
        start_time = time.time()
        import random
        [random.randint(0, 100) for _ in range(1000)]
        end_time = time.time()
        python_latency = (end_time - start_time) * 1000
        ratio = latency / python_latency
        print(f'BENCHMARK:vs_python_latency_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance:{str(e)}')

def measure_memory():
    try:
        import boringbar
        # Create synthetic data
        data = [random.randint(0, 100) for _ in range(1000)]
        tracemalloc.start()
        boringbar.run(data)
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:boringbar_memory_mb:{peak / (1024 * 1024)}')
        tracemalloc.stop()
    except Exception as e:
        print(f'TEST_FAIL:measure_memory:{str(e)}')

def count_loc():
    try:
        import os
        loc_count = 0
        for root, dirs, files in os.walk('./boringbar'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        loc_count += len(f.readlines())
        print(f'BENCHMARK:loc_count:{loc_count}')
    except Exception as e:
        print(f'TEST_FAIL:count_loc:{str(e)}')

def count_test_files():
    try:
        import os
        test_files_count = 0
        for root, dirs, files in os.walk('./boringbar'):
            for file in files:
                if file.endswith('_test.py'):
                    test_files_count += 1
        print(f'BENCHMARK:test_files_count:{test_files_count}')
    except Exception as e:
        print(f'TEST_FAIL:count_test_files:{str(e)}')

install_boringbar()
test_basic_run()
test_performance()
compare_performance()
measure_memory()
count_loc()
count_test_files()
print('RUN_OK')