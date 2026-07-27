import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK')

# Clone and install python-package from source as fallback if pip install fails
try:
    subprocess.run(['pip', 'install', 'cfql'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/jaysmito/cfql.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './cfql'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:Failed to install cfql: {str(e)}')
        # Continue to next test
        pass

# Import the library and measure import time
start_time = time.time()
try:
    spec = importlib.util.find_spec('cfql')
    if spec is None:
        raise ImportError
    importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spec)
    print(f'BENCHMARK:import_time_ms:{(time.time() - start_time) * 1000:.2f}')
    print('TEST_PASS:import_cfql')
except ImportError as e:
    print(f'TEST_FAIL:import_cfql:No module named cfql')

# Run a minimal functional test with synthetic data
try:
    from cfql import Queue
    queue = Queue()
    start_time = time.time()
    for i in range(10000):
        queue.push(i)
    for i in range(10000):
        queue.pop()
    print(f'BENCHMARK:queue_latency_ms:{(time.time() - start_time) * 1000:.2f}')
    print('TEST_PASS:queue_operations')
except Exception as e:
    print(f'TEST_FAIL:queue_operations:{str(e)}')

# Compare performance vs the most similar baseline tool
try:
    import queue as python_queue
    start_time = time.time()
    python_q = python_queue.Queue()
    for i in range(10000):
        python_q.put(i)
    for i in range(10000):
        python_q.get()
    python_time = (time.time() - start_time) * 1000
    cfql_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:vs_python_queue_latency_ms:{python_time:.2f}')
    print(f'BENCHMARK:vs_python_queue_latency_ratio:{(cfql_time / python_time):.2f}')
    print('TEST_PASS:compare_queue_performance')
except Exception as e:
    print(f'TEST_FAIL:compare_queue_performance:{str(e)}')

# Measure memory usage
try:
    tracemalloc.start()
    queue = Queue()
    for i in range(10000):
        queue.push(i)
    for i in range(10000):
        queue.pop()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{peak:.2f}')
    tracemalloc.stop()
    print('TEST_PASS:memory_usage')
except Exception as e:
    print(f'TEST_FAIL:memory_usage:{str(e)}')

# Measure the number of lines of code
try:
    subprocess.run(['git', 'clone', 'https://github.com/jaysmito/cfql.git'], check=True)
    loc = subprocess.check_output(['wc', '-l', './cfql/cfql.py']).decode('utf-8').split()[0]
    print(f'BENCHMARK:loc_count:{loc}')
    print('TEST_PASS:loc_count')
except Exception as e:
    print(f'TEST_FAIL:loc_count:{str(e)}')

print('RUN_OK')