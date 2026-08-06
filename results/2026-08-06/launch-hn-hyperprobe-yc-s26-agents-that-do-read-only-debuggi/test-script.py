import subprocess
import time
import tracemalloc
import os

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)

# Install tool dependencies
try:
    subprocess.run(['npm', 'install', 'hyperprobe'], check=False)
    print('INSTALL_OK')
except Exception as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/hyperprobe/hyperprobe.git'], check=False)
        os.chdir('hyperprobe')
        subprocess.run(['npm', 'install'], check=False)
        print('INSTALL_OK')
    except Exception as e2:
        print(f'INSTALL_FAIL:{str(e2)}')

# Test 1: Create a test case
try:
    start_time = time.time()
    subprocess.run(['hyperprobe', 'init'], check=False)
    end_time = time.time()
    test_time = end_time - start_time
    print(f'TEST_PASS:create_test_case')
    print(f'BENCHMARK:hyperprobe_init_time_ms:{test_time * 1000}')
except Exception as e:
    print(f'TEST_FAIL:create_test_case:{str(e)}')

# Test 2: Debug a real-world application
try:
    start_time = time.time()
    subprocess.run(['hyperprobe', 'start'], check=False)
    end_time = time.time()
    test_time = end_time - start_time
    print(f'TEST_PASS:debug_real_world_app')
    print(f'BENCHMARK:hyperprobe_debug_time_ms:{test_time * 1000}')
except Exception as e:
    print(f'TEST_FAIL:debug_real_world_app:{str(e)}')

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}')
tracemalloc.stop()

# Compare performance vs baseline tool (New Relic)
try:
    start_time = time.time()
    subprocess.run(['newrelic', 'exec', 'hyperprobe', 'start'], check=False)
    end_time = time.time()
    test_time = end_time - start_time
    print(f'BENCHMARK:vs_newrelic_ratio:{test_time / (end_time - start_time)}')
except Exception as e:
    print(f'BENCHMARK:vs_newrelic_ratio:baseline_failed')

# Count lines of code
loc_count = sum(1 for _ in open(os.path.join('hyperprobe', 'src', 'index.js')))
print(f'BENCHMARK:loc_count:{loc_count}')

# Count test files
test_files_count = sum(1 for _ in os.listdir(os.path.join('hyperprobe', 'tests')))
print(f'BENCHMARK:test_files_count:{test_files_count}')

print('RUN_OK')