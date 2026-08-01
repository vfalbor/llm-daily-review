import subprocess
import time
import tracemalloc
import importlib.util
import random

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'longrange'], check=True)
except subprocess.CalledProcessError:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/unknown/longrange.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './longrange'], cwd='./longrange', check=True)
    except subprocess.CalledProcessError:
        print('INSTALL_FAIL: unable to install longrange')
        print('RUN_OK')
        exit(1)

print('INSTALL_OK')

# Load the longrange module
spec = importlib.util.find_spec('longrange')
if spec is None:
    print('TEST_FAIL:longrange_import: unable to import longrange')
else:
    longrange = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(longrange)
        print('TEST_PASS:longrange_import')
    except Exception as e:
        print(f'TEST_FAIL:longrange_import:{str(e)}')

# Measure import time
start_time = time.time()
importlib.reload(longrange)
end_time = time.time()
import_time_ms = (end_time - start_time) * 1000
print(f'BENCHMARK:import_time_ms:{import_time_ms}')

# Measure core operation latency
def generate_synthetic_data():
    return [random.random() for _ in range(1000)]

start_time = time.time()
longrange.process_data(generate_synthetic_data())
end_time = time.time()
operation_time_ms = (end_time - start_time) * 1000
print(f'BENCHMARK:operation_time_ms:{operation_time_ms}')

# Measure memory usage
tracemalloc.start()
longrange.process_data(generate_synthetic_data())
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_bytes:{peak}')

# Compare vs similar tool
try:
    import wifi
    start_time = time.time()
    wifi.process_data(generate_synthetic_data())
    end_time = time.time()
    similar_tool_time_ms = (end_time - start_time) * 1000
    ratio = operation_time_ms / similar_tool_time_ms
    print(f'BENCHMARK:vs_wifi_operation_time_ratio:{ratio}')
except ImportError:
    print('TEST_SKIP:vs_wifi_comparison: unable to import wifi')

print('RUN_OK')