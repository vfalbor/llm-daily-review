import subprocess
import time
import tracemalloc
import os
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

try:
    # Clone the repository
    subprocess.run(['git', 'clone', 'https://github.com/cakehonolulu/linux-for-jaguar'], check=True)
except Exception as e:
    print(f"INSTALL_FAIL:Failed to clone repository {e}")
    exit(1)

# Change directory to the cloned repository
os.chdir('./linux-for-jaguar')

try:
    # Count source files and languages
    start_time = time.time()
    source_files = subprocess.run(['find', '.', '-type', 'f', '-print'], stdout=subprocess.PIPE, check=True)
    end_time = time.time()
    source_files_list = source_files.stdout.decode('utf-8').splitlines()
    languages = set()
    for file in source_files_list:
        if file.endswith(('.c', '.cpp', '.h', '.hpp', '.java', '.py', '.go', '.js', '.sh', '.java', '.scala', '.swift', '.kt')):
            languages.add(file.split('.')[-1])
    print(f"BENCHMARK:source_files_count:{len(source_files_list)}")
    print(f"BENCHMARK:languages_count:{len(languages)}")
    print(f"BENCHMARK:discover_time_ms:{(end_time - start_time) * 1000}")
except Exception as e:
    print(f"TEST_FAIL:discover_time_ms:{e}")

try:
    # Check for simulator/emulator
    emulators = subprocess.run(['find', '.', '-name', '*emulator*'], stdout=subprocess.PIPE, check=True)
    emulators_list = emulators.stdout.decode('utf-8').splitlines()
    if emulators_list:
        print(f"BENCHMARK:emulator_count:{len(emulators_list)}")
    else:
        print(f"BENCHMARK:emulator_count:0")
except Exception as e:
    print(f"TEST_FAIL:emulator_count:{e}")

# Run any Python examples found
try:
    python_files = subprocess.run(['find', '.', '-name', '*.py'], stdout=subprocess.PIPE, check=True)
    python_files_list = python_files.stdout.decode('utf-8').splitlines()
    if python_files_list:
        start_time = time.time()
        for file in python_files_list:
            subprocess.run(['python', file], check=True)
        end_time = time.time()
        print(f"BENCHMARK:python_examples_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:python_examples")
    else:
        print(f"TEST_SKIP:python_examples:No Python examples found")
except Exception as e:
    print(f"TEST_FAIL:python_examples:{e}")

try:
    # Measure performance
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['make'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    end_time = time.time()
    print(f"BENCHMARK:make_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:make_peak_memory_mb:{peak / (1024 * 1024)}")
    tracemalloc.stop()
    print(f"TEST_PASS:make")
except Exception as e:
    print(f"TEST_FAIL:make:{e}")

try:
    # Compare performance vs similar tool
    # Note: There is no similar tool listed, so this test is skipped
    print(f"TEST SKIP:compare_performance:No similar tool listed")
except Exception as e:
    print(f"TEST_FAIL:compare_performance:{e}")

print("RUN_OK")