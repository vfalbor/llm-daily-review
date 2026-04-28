import subprocess
import time
import tracemalloc
import os
import gitperf

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL: {e}')

def install_tool_dependencies():
    try:
        subprocess.run(['pip', 'install', 'gitperf'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL: {e}')
        try:
            subprocess.run(['git', 'clone', 'https://github.com/gitperf/gitperf.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './gitperf'], check=True)
            print('INSTALL_OK')
        except subprocess.CalledProcessError as e:
            print(f'INSTALL_FAIL: {e}')

def test_clone_performance():
    try:
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/git/git.git'], check=True)
        end_time = time.time()
        checkout_time = end_time - start_time
        print(f'BENCHMARK:clone_time_s:{checkout_time}')
        print(f'TEST_PASS:clone_performance')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:clone_performance: {e}')
    except Exception as e:
        print(f'TEST_FAIL:clone_performance: {e}')

def test_import_time():
    try:
        start_time = time.time()
        import gitperf
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:import_time_ms:{import_time}')
        print(f'TEST_PASS:import_time')
    except Exception as e:
        print(f'TEST_FAIL:import_time: {e}')

def test_core_operation_latency():
    try:
        start_time = time.time()
        gitperf.core_operation()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:core_operation_latency_ms:{latency}')
        print(f'TEST_PASS:core_operation_latency')
    except Exception as e:
        print(f'TEST_FAIL:core_operation_latency: {e}')

def compare_performance():
    try:
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/git/git.git'], check=True)
        end_time = time.time()
        vanilla_git_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['gitperf', 'clone', 'https://github.com/git/git.git'], check=True)
        end_time = time.time()
        gitperf_time = end_time - start_time
        ratio = gitperf_time / vanilla_git_time
        print(f'BENCHMARK:vs_vanilla_git_clone_ratio:{ratio}')
        print(f'TEST_PASS:compare_performance')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:compare_performance: {e}')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance: {e}')

def measure_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['gitperf', 'clone', 'https://github.com/git/git.git'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_mb:{peak / 10**6}')
        tracemalloc.stop()
        print(f'TEST_PASS:memory_usage')
    except Exception as e:
        print(f'TEST_FAIL:memory_usage: {e}')

def count_test_files():
    try:
        count = len(os.listdir('./tests'))
        print(f'BENCHMARK:test_files_count:{count}')
        print(f'TEST_PASS:count_test_files')
    except Exception as e:
        print(f'TEST_FAIL:count_test_files: {e}')

def count_lines_of_code():
    try:
        count = 0
        for root, dirs, files in os.walk('./gitperf'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        count += len(f.readlines())
        print(f'BENCHMARK:loc_count:{count}')
        print(f'TEST_PASS:count_lines_of_code')
    except Exception as e:
        print(f'TEST_FAIL:count_lines_of_code: {e}')

install_packages()
install_tool_dependencies()
test_clone_performance()
test_import_time()
test_core_operation_latency()
compare_performance()
measure_memory_usage()
count_test_files()
count_lines_of_code()
print('RUN_OK')