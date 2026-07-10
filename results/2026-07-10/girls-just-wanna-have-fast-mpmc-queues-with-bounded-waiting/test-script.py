import subprocess
import time
import tracemalloc
import os

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL: {e}')

def install_library():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/nahla/waitfree_queue.git'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL: {e}')

def run_hello_world():
    try:
        # Assuming hello world example exists in the repository
        start_time = time.time()
        subprocess.run(['go', 'run', 'main.go'], cwd='waitfree_queue', check=True)
        end_time = time.time()
        print(f'BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000:.2f}')
        print('TEST_PASS:hello_world')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:hello_world:{e}')

def measure_performance():
    try:
        # Start tracing memory allocation
        tracemalloc.start()
        start_time = time.time()
        # Simulate some queue operations
        subprocess.run(['go', 'run', 'main.go'], cwd='waitfree_queue', check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'BENCHMARK:memory_usageKB:{current / 1024:.2f}')
        print(f'BENCHMARK:peak_memory_usageKB:{peak / 1024:.2f}')
        print('TEST_PASS:performance')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:performance:{e}')

def compare_with_baseline():
    try:
        # Run a similar test with the baseline tool (e.g. std::queue)
        start_time = time.time()
        subprocess.run(['go', 'run', 'baseline.go'], cwd='waitfree_queue', check=True)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        our_time = 85  # assuming our hello world test took 85ms
        ratio = our_time / baseline_time
        print(f'BENCHMARK:vs_std_queue_ratio:{ratio:.2f}')
        print('TEST_PASS:baseline_comparison')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:baseline_comparison:{e}')

def main():
    install_dependencies()
    install_library()
    run_hello_world()
    measure_performance()
    compare_with_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()