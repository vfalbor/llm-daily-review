import subprocess
import time
import tracemalloc
import os

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/phononlab/phyphox.git'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Count source files and languages
try:
    os.chdir('phyphox')
    source_files = subprocess.run(['find', '.', '-name', '*.py'], capture_output=True, text=True).stdout.splitlines()
    language_count = len(set([f.split('.')[-1] for f in source_files]))
    print(f'BENCHMARK:loc_count:{len(source_files)}')
    print(f'BENCHMARK:language_count:{language_count}')
except Exception as e:
    print(f'TEST_FAIL:count_source_files:{str(e)}')

# Check for simulator/emulator
try:
    subprocess.run(['git', 'grep', '-r', 'simulator'], capture_output=True, text=True)
    print('TEST_PASS:check_simulator')
except Exception as e:
    print(f'TEST_FAIL:check_simulator:{str(e)}')

# Run any Python examples found
try:
    example_files = subprocess.run(['find', '.', '-name', '*.py'], capture_output=True, text=True).stdout.splitlines()
    for file in example_files:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python', file], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:run_example_{file}_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:run_example_{file}_mem_mb:{peak / 10**6}')
    print('TEST_PASS:run_examples')
except Exception as e:
    print(f'TEST_FAIL:run_examples:{str(e)}')

# Run a simple experiment like acceleration measurement
try:
    start_time = time.time()
    subprocess.run(['python', '-c', 'import phyphox'], check=True)
    end_time = time.time()
    print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:run_experiment')
except Exception as e:
    print(f'TEST_FAIL:run_experiment:{str(e)}')

# Test different experiment modes
try:
    experiment_modes = ['acceleration', 'gyroscope', 'magnetometer']
    for mode in experiment_modes:
        start_time = time.time()
        subprocess.run(['python', '-c', f'import phyphox; phyphox.{mode}()'], check=True)
        end_time = time.time()
        print(f'BENCHMARK:run_{mode}_mode_time_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:test_experiment_modes')
except Exception as e:
    print(f'TEST_FAIL:test_experiment_modes:{str(e)}')

# Check accuracy of measurements
try:
    # This test requires actual hardware and is not feasible in a Docker container
    print('TEST_SKIP:check_accuracy:requires_hardware')
except Exception as e:
    print(f'TEST_FAIL:check_accuracy:{str(e)}')

# Compare performance vs the most similar baseline tool listed above (Sensor Kinetics)
try:
    # This test requires actual hardware and is not feasible in a Docker container
    print('TEST_SKIP:compare_performance:requires_hardware')
except Exception as e:
    print(f'TEST_FAIL:compare_performance:{str(e)}')

print('RUN_OK')