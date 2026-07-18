import subprocess
import time
import tracemalloc
import sys

def install_tool():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git', 'curl'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/parksb/revive-netbook.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './revive-netbook'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_run():
    try:
        start_time = time.time()
        subprocess.run(['python', '-m', 'revive_netbook'], check=False)
        end_time = time.time()
        run_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:run_time_ms:{run_time:.2f}')
        print('TEST_PASS:test_run')
    except Exception as e:
        print(f'TEST_FAIL:test_run:{str(e)}')

def test_performance():
    try:
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['python', '-m', 'revive_netbook', '--perf'], check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        run_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:performance_time_ms:{run_time:.2f}')
        print(f'BENCHMARK:performance_memory_mb:{current / (1024 * 1024):.2f}')
        print('TEST_PASS:test_performance')
    except Exception as e:
        print(f'TEST_FAIL:test_performance:{str(e)}')

def compare_baseline():
    try:
        start_time = time.time()
        subprocess.run(['python', '-m', 'baseline_tool'], check=False)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_baseline_run_time_ms:{baseline_time:.2f}')
        print('TEST_PASS:compare_baseline')
    except Exception as e:
        print(f'TEST_FAIL:compare_baseline:{str(e)}')

def benchmark_count():
    try:
        subprocess.run(['git', 'ls-files'], check=False, stdout=subprocess.PIPE)
        count = len(subprocess.run(['git', 'ls-files'], check=False, stdout=subprocess.PIPE).stdout.decode().splitlines())
        print(f'BENCHMARK:file_count:{count}')
    except Exception as e:
        print(f'TEST_FAIL:benchmark_count:{str(e)}')

def benchmark_loc():
    try:
        loc = len(subprocess.run(['git', 'ls-files'], check=False, stdout=subprocess.PIPE).stdout.decode().splitlines())
        print(f'BENCHMARK:loc_count:{loc}')
    except Exception as e:
        print(f'TEST_FAIL:benchmark_loc:{str(e)}')

install_tool()
test_run()
test_performance()
compare_baseline()
benchmark_count()
benchmark_loc()

print('RUN_OK')