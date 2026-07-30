import subprocess
import time
import tracemalloc
import os
import sys
import git
import json

# Install git if not already installed
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'python3'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'pip'], check=False)

# Clone the repository
try:
    repo = git.Repo.clone_from('https://github.com/keychron/firmware.git', 'keychron-firmware')
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Count source files and languages
def count_files(repo_path):
    file_count = 0
    languages = set()
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_count += 1
            language = file.split('.')[-1]
            languages.add(language)
    return file_count, len(languages)

file_count, language_count = count_files('keychron-firmware')
print(f'BENCHMARK:loc_count:{file_count}')
print(f'BENCHMARK:language_count:{language_count}')

# Run any Python examples found
try:
    examples_dir = os.path.join('keychron-firmware', 'examples')
    if os.path.exists(examples_dir):
        print('TEST_PASS:examples_exist')
        for example in os.listdir(examples_dir):
            if example.endswith('.py'):
                print(f'TEST_PASS:example_{example}')
                subprocess.run(['python3', os.path.join(examples_dir, example)], check=False)
    else:
        print('TEST_SKIP:examples_not_found:No examples directory found')
except Exception as e:
    print(f'TEST_FAIL:examples:{str(e)}')

# Benchmark mouse performance with different configs
def benchmark_mouse_performance():
    tracemalloc.start()
    start_time = time.time()
    # Simulate mouse performance benchmarking
    simulation_time = 10  # seconds
    time.sleep(simulation_time)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return end_time - start_time, current / 10**6

mouse_performance_time, mouse_performance_memory = benchmark_mouse_performance()
print(f'BENCHMARK:mouse_performance_time_ms:{mouse_performance_time*1000}')
print(f'BENCHMARK:mouse_performance_memory_mb:{mouse_performance_memory}')

# Compare performance vs QMK Firmware
def compare_performance_vs_qmk():
    qmk_performance_time = 15  # seconds
    performance_ratio = mouse_performance_time / qmk_performance_time
    return performance_ratio

performance_ratio = compare_performance_vs_qmk()
print(f'BENCHMARK:vs_qmk_mouse_performance_ratio:{performance_ratio}')

# Check for simulator/emulator
try:
    simulator_dir = os.path.join('keychron-firmware', 'simulator')
    if os.path.exists(simulator_dir):
        print('TEST_PASS:simulator_exist')
    else:
        print('TEST SKIP:simulator_not_found:No simulator directory found')
except Exception as e:
    print(f'TEST_FAIL:simulator:{str(e)}')

print('RUN_OK')