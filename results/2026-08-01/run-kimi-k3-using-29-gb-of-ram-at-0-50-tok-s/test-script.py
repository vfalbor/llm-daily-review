import subprocess
import sys
import time
import tracemalloc
import importlib.util

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install pip
subprocess.run(['apk', 'add', '--no-cache', 'python3-dev'], check=False)
subprocess.run(['pip3', 'install', '--upgrade', 'pip'], check=False)

# Install waste using pip
try:
    subprocess.run(['pip3', 'install', 'waste'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

    # Try installing from source as fallback
    subprocess.run(['git', 'clone', 'https://github.com/sqliteai/waste.git'], check=True)
    subprocess.run(['pip3', 'install', '-e', './waste'], check=True)
    print('INSTALL_OK')

# Measure import time
import_time_start = time.time()
try:
    import waste
    import_time_end = time.time()
    print(f'BENCHMARK:import_time_ms:{(import_time_end - import_time_start) * 1000:.2f}')
except Exception as e:
    print(f'TEST_FAIL:import_waste:{str(e)}')

# Test 1: Install waste and measure memory usage
try:
    tracemalloc.start()
    waste_instance = waste.Waste()
    tracemalloc.stop()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{current}')
    print(f'BENCHMARK:peak_memory_usage_bytes:{peak}')
    print('TEST_PASS:install_waste')
except Exception as e:
    print(f'TEST_FAIL:install_waste:{str(e)}')

# Test 2: Use waste to track down memory leak
try:
    tracemalloc.start()
    waste_instance.track_memory()
    tracemalloc.stop()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_leak_detection_bytes:{current}')
    print(f'BENCHMARK:peak_memory_leak_detection_bytes:{peak}')
    print('TEST_PASS:track_memory_leak')
except Exception as e:
    print(f'TEST_FAIL:track_memory_leak:{str(e)}')

# Test 3: Compare waste with other memory profilers
try:
    subprocess.run(['pip3', 'install', 'memory_profiler'], check=True)
    import memory_profiler
    tracemalloc.start()
    memory_profiler.memory_usage((waste_instance.track_memory, ), interval=.01)
    tracemalloc.stop()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:vs_memory_profiler_memory_usage_bytes:{current}')
    print(f'BENCHMARK:vs_memory_profiler_peak_memory_usage_bytes:{peak}')
    print('TEST_PASS:compare_memory_profilers')
except Exception as e:
    print(f'TEST_FAIL:compare_memory_profilers:{str(e)}')

# Measure execution time
execution_time_start = time.time()
try:
    waste_instance.track_memory()
    execution_time_end = time.time()
    print(f'BENCHMARK:execution_time_ms:{(execution_time_end - execution_time_start) * 1000:.2f}')
except Exception as e:
    print(f'TEST_FAIL:execution_time:{str(e)}')

# Compare performance vs memory_profiler
try:
    import memory_profiler
    tracemalloc.start()
    execution_time_start = time.time()
    memory_profiler.memory_usage((waste_instance.track_memory, ), interval=.01)
    execution_time_end = time.time()
    tracemalloc.stop()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:vs_memory_profiler_execution_time_ms:{(execution_time_end - execution_time_start) * 1000:.2f}')
    print(f'BENCHMARK:vs_memory_profiler_memory_usage_bytes:{current}')
    print(f'BENCHMARK:vs_memory_profiler_peak_memory_usage_bytes:{peak}')
except Exception as e:
    print(f'TEST_FAIL:compare_execution_time:{str(e)}')

# Measure and emit loc count
try:
    import os
    loc_count = 0
    for root, dirs, files in os.walk('./waste'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += len(f.readlines())
    print(f'BENCHMARK:loc_count:{loc_count}')
except Exception as e:
    print(f'TEST_FAIL:loc_count:{str(e)}')

print('RUN_OK')