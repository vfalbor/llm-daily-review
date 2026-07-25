import subprocess
import time
import tracemalloc
import json
import os

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Clone repository and install from source
try:
    subprocess.run(['git', 'clone', 'https://github.com/user/globaloilnetwork.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './globaloilnetwork'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Test CLI availability
try:
    subprocess.run(['python', '-c', 'import globaloilnetwork'], check=True)
    print('TEST_PASS:cli_availability')
except Exception as e:
    print(f'TEST_FAIL:cli_availability:{str(e)}')

# Run simulation with different chokepoint percentages
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['python', '-c', 'import globaloilnetwork; globaloilnetwork.run_simulation(0.5)'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:simulation_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:simulation_memory_bytes:{peak}')
    print('TEST_PASS:simulation')
except Exception as e:
    print(f'TEST_FAIL:simulation:{str(e)}')

# Compare simulation results against historical closure data
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['python', '-c', 'import globaloilnetwork; globaloilnetwork.compare_simulation_results()'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:comparison_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:comparison_memory_bytes:{peak}')
    print('TEST_PASS:comparison')
except Exception as e:
    print(f'TEST_FAIL:comparison:{str(e)}')

# Analyze the impact on oil prices during closure
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['python', '-c', 'import globaloilnetwork; globaloilnetwork.analyze_oil_prices()'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:analysis_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:analysis_memory_bytes:{peak}')
    print('TEST_PASS:analysis')
except Exception as e:
    print(f'TEST_FAIL:analysis:{str(e)}')

# Compare performance vs the most similar baseline tool (Stratfor)
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['python', '-c', 'import stratfor; stratfor.run_simulation(0.5)'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    baseline_time = (end_time - start_time) * 1000
    baseline_memory = peak
    print(f'BENCHMARK:vs_stratfor_simulation_time_ms:{baseline_time}')
    print(f'BENCHMARK:vs_stratfor_simulation_memory_bytes:{baseline_memory}')
    print(f'BENCHMARK:vs_stratfor_simulation_ratio:{(end_time - start_time) / baseline_time}')
    print('TEST_PASS:baseline_comparison')
except Exception as e:
    print(f'TEST_FAIL:baseline_comparison:{str(e)}')

print('RUN_OK')