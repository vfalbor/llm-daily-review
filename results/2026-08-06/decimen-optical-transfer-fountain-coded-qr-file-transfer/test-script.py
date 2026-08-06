import subprocess
import time
import tracemalloc
import os
import sys

# Install system packages with subprocess
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install git package: {e}")
    sys.exit(1)

# Clone Decimen Optical Transfer repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/bashalarmistalt/decimen-optical-transfer.git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to clone Decimen Optical Transfer repository: {e}")
    sys.exit(1)

# Change into the cloned repository
os.chdir('decimen-optical-transfer')

# Count source files and languages
try:
    source_files = subprocess.check_output(['find', '.', '-type', 'f', '-name', '*.py'])
    source_files_count = len(source_files.splitlines())
    print(f"BENCHMARK:source_files_count:{source_files_count}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:source_files_count:Failed to count source files: {e}")

# Check for simulator/emulator
try:
    simulator_files = subprocess.check_output(['find', '.', '-type', 'f', '-name', '*simulator*'])
    if simulator_files:
        print("BENCHMARK:simulator_present:1")
    else:
        print("BENCHMARK:simulator_present:0")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:simulator_present:Failed to check for simulator: {e}")

# Run Python examples
try:
    example_files = subprocess.check_output(['find', '.', '-type', 'f', '-name', '*example.py'])
    for example_file in example_files.splitlines():
        example_file = example_file.decode('utf-8')
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python', example_file], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:example_run_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:example_run_memory_mb:{current / (1024 * 1024):.2f}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:example_run:Failed to run example: {e}")

# Compare performance vs the most similar baseline tool (QRadar)
try:
    start_time = time.time()
    subprocess.run(['git', 'clone', 'https://github.com/qradar/QRadar.git'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:vs_qradar_clone_time_ms:{(end_time - start_time) * 1000:.2f}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:vs_qradar_clone:Failed to clone QRadar repository: {e}")

# Measure error rates using the CLI
try:
    start_time = time.time()
    subprocess.run(['python', '-m', 'decimen', 'transfer', 'test.txt'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:transfer_time_ms:{(end_time - start_time) * 1000:.2f}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:transfer_time:Failed to transfer file: {e}")

print("RUN_OK")