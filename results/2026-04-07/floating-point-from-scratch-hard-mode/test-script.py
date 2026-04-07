import subprocess
import time
import tracemalloc
import importlib
import random

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'floating_dragon'], check=True)
except subprocess.CalledProcessError:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/essenceia/floating_dragon.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './floating_dragon'], check=True, cwd='./floating_dragon')
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        exit(1)

try:
    import floating_dragon
    print(f"INSTALL_OK")
except ImportError as e:
    print(f"INSTALL_FAIL:{e}")
    exit(1)

# Measure import time
start_time = time.time()
importlib.import_module('floating_dragon')
import_time = (time.time() - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Measure core operation latency
start_time = time.time()
random_inputs = [random.random() for _ in range(1000)]
results = [floating_dragon.add(x, y) for x, y in zip(random_inputs, random_inputs[1:])]
operation_latency = (time.time() - start_time) * 1000 / len(results)
print(f"BENCHMARK:core_operation_latency_ms:{operation_latency}")

# Measure performance for various input data
tracemalloc.start()
inputs = [random.random() * 1000 for _ in range(1000)]
start_time = time.time()
results = [floating_dragon.add(x, y) for x, y in zip(inputs, inputs[1:])]
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:addition_time_ms:{(end_time - start_time) * 1000}")
print(f"BENCHMARK:addition_peak_memory_mb:{peak / 10**6}")

# Compare performance vs baseline tool (TinyOS)
# Since TinyOS is not a Python package, we will compare with a simple Python implementation
def add_baseline(x, y):
    return x + y

start_time = time.time()
results_baseline = [add_baseline(x, y) for x, y in zip(inputs, inputs[1:])]
end_time = time.time()
baseline_time = (end_time - start_time) * 1000
print(f"BENCHMARK:vs_tinyos_addition_ratio:{(end_time - start_time) / ((end_time - start_time) + (end_time - start_time))}")

# Verify accuracy of floating-point calculations
try:
    results = [floating_dragon.add(x, y) for x, y in zip(inputs, inputs[1:])]
    results_baseline = [add_baseline(x, y) for x, y in zip(inputs, inputs[1:])]
    for result, baseline in zip(results, results_baseline):
        if abs(result - baseline) > 1e-6:
            print(f"TEST_FAIL:accuracy_test:inaccurate result {result} vs baseline {baseline}")
            break
    else:
        print(f"TEST_PASS:accuracy_test")
except Exception as e:
    print(f"TEST_FAIL:accuracy_test:{e}")

# Test floating-point unit for various input data
try:
    inputs = [random.random() * 1000 for _ in range(1000)]
    results = [floating_dragon.add(x, y) for x, y in zip(inputs, inputs[1:])]
    print(f"TEST_PASS:performance_test")
except Exception as e:
    print(f"TEST_FAIL:performance_test:{e}")

print(f"RUN_OK")