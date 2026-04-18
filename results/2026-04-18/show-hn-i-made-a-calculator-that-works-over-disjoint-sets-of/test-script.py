import subprocess
import importlib
import time
import tracemalloc
from interval_calculator import IntervalCalculator

# Install required system packages
print('Installing required system packages...')
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install the calculator
print('Installing the interval calculator...')
try:
    subprocess.run(['pip', 'install', 'interval-calculator'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError:
    print('INSTALL_FAIL:pip install failed')
    try:
        subprocess.run(['git', 'clone', 'https://github.com/victorpoughon/interval-calculator.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './interval-calculator'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError:
        print('INSTALL_FAIL:git clone and pip install -e failed')

# Measure import time
print('Measuring import time...')
import_start_time = time.time()
try:
    importlib.import_module('interval_calculator')
    import_end_time = time.time()
    import_time = (import_end_time - import_start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
except ImportError as e:
    print(f'TEST_FAIL:import_time:failed to import')
    print(f'BENCHMARK:import_time_ms:INF')

# Test the calculator with sample intervals
print('Testing the calculator with sample intervals...')
calculator = IntervalCalculator()
intervals = [(1, 2), (3, 4), (5, 6)]
try:
    result = calculator.calculate(intervals)
    manual_result = [1, 2, 3, 4, 5, 6]
    if result == manual_result:
        print('TEST_PASS:interval_calculator')
    else:
        print('TEST_FAIL:interval_calculator:')
    tracemalloc.start()
    start_time = time.time()
    calculator.calculate(intervals)
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:calculator_latency_ms:{latency:.2f}')
    print(f'BENCHMARK:calculator_memory_mb:{current / 1024 / 1024:.2f}')
except Exception as e:
    print(f'TEST_FAIL:interval_calculator:{str(e)}')

# Compare performance with a baseline tool (Interval arithmetic)
print('Comparing performance with a baseline tool...')
try:
    import interval_arithmetic
    baseline_calculator = interval_arithmetic.IntervalCalculator()
    start_time = time.time()
    baseline_calculator.calculate(intervals)
    end_time = time.time()
    baseline_latency = (end_time - start_time) * 1000
    ratio = latency / baseline_latency
    print(f'BENCHMARK:vs_interval_arithmetic_latency_ratio:{ratio:.2f}')
    print(f'BENCHMARK:vs_interval_arithmetic_latency_ms:{baseline_latency:.2f}')
except ImportError:
    print('TEST_SKIP:baseline_comparison:Interval arithmetic not found')

print('RUN_OK')