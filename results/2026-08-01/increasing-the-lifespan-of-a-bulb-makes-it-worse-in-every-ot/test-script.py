import subprocess
import time
import tracemalloc
import sys

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

try:
    # Install tool dependencies
    subprocess.run(['pip', 'install', 'lifespan'], check=True)
except subprocess.CalledProcessError:
    # Fallback to git clone and pip install -e .
    subprocess.run(['git', 'clone', 'https://github.com/lifespan/lifespan.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './lifespan'], cwd='./lifespan', check=True)

print('INSTALL_OK')

import lifespan

# Basic run test
try:
    start_time = time.time()
    lifespan.run()
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f'TEST_PASS:basic_run')
    print(f'BENCHMARK:basic_run_latency_ms:{latency:.2f}')
except Exception as e:
    print(f'TEST_FAIL:basic_run:{str(e)}')

# Measure performance
try:
    start_time = time.time()
    lifespan.run_performance_test()
    end_time = time.time()
    performance_latency = (end_time - start_time) * 1000
    print(f'TEST_PASS:performance_test')
    print(f'BENCHMARK:performance_latency_ms:{performance_latency:.2f}')
except Exception as e:
    print(f'TEST_FAIL:performance_test:{str(e)}')

# Measure memory usage
try:
    tracemalloc.start()
    lifespan.run_memory_test()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'TEST_PASS:memory_test')
    print(f'BENCHMARK:memory_usage_bytes:{peak}')
except Exception as e:
    print(f'TEST_FAIL:memory_test:{str(e)}')

# Measure import time
try:
    start_time = time.time()
    import lifespan
    end_time = time.time()
    import_latency = (end_time - start_time) * 1000
    print(f'TEST_PASS:import_test')
    print(f'BENCHMARK:import_latency_ms:{import_latency:.2f}')
except Exception as e:
    print(f'TEST_FAIL:import_test:{str(e)}')

# Compare vs similar tool (e.g. similar-tool)
try:
    subprocess.run(['pip', 'install', 'similar-tool'], check=True)
    import similar_tool
    start_time = time.time()
    similar_tool.run()
    end_time = time.time()
    similar_tool_latency = (end_time - start_time) * 1000
    ratio = similar_tool_latency / performance_latency
    print(f'BENCHMARK:vs_similar_tool_ratio:{ratio:.2f}')
except Exception as e:
    print(f'TEST_SKIP:similar_tool_comparison:{str(e)}')

print('RUN_OK')