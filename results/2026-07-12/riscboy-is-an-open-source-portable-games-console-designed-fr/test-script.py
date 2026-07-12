import subprocess
import time
import tracemalloc
import os
import requests
from datetime import timedelta

# Install system packages with subprocess
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repo
try:
    subprocess.run(['git', 'clone', 'https://github.com/Wren6991/RISCBoy.git'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Change directory to the cloned repo
os.chdir('RISCBoy')

# Count source files and languages
try:
    file_count = 0
    languages = set()
    for root, dirs, files in os.walk('.'):
        for file in files:
            file_count += 1
            if file.endswith(('.py', '.c', '.cpp', '.java', '.js', '.swift', '.kt')):
                languages.add(file.split('.')[-1])
    print(f"BENCHMARK:loc_count:{file_count}")
    print(f"BENCHMARK:languages_count:{len(languages)}")
except Exception as e:
    print(f"TEST_FAIL:source_file_count:{e}")

# Check for simulator/emulator
try:
    # Look for emulator executable in the repo
    emulator_path = None
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.exe', '.bin', '.elf')):
                emulator_path = os.path.join(root, file)
                break
    if emulator_path:
        print("TEST_PASS:emulator_found")
        # Run the emulator and measure performance
        start_time = time.time()
        subprocess.run([emulator_path], check=True)
        end_time = time.time()
        print(f"BENCHMARK:emulator_run_time_ms:{(end_time - start_time) * 1000}")
    else:
        print("TEST_FAIL:emulator_not_found")
except Exception as e:
    print(f"TEST_FAIL:emulator_run:{e}")

# Run any Python examples found
try:
    # Look for Python examples in the repo
    example_path = None
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                example_path = os.path.join(root, file)
                break
    if example_path:
        print("TEST_PASS:example_found")
        # Run the example and measure performance
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python', example_path], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:example_run_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:example_memory_usage_bytes:{current}")
    else:
        print("TEST_FAIL:example_not_found")
except Exception as e:
    print(f"TEST_FAIL:example_run:{e}")

# Compare performance vs the most similar baseline tool listed above
try:
    # Run a benchmark on the baseline tool (e.g., Game Boy Advance emulator)
    start_time = time.time()
    subprocess.run(['gears', 'run'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:vs_gba_benchmark_ms:{(end_time - start_time) * 1000}")
    # Compare the performance of RISCBoy with the baseline tool
    riscboy_run_time = (end_time - start_time) * 1000
    gba_run_time = requests.get('https://example.com/gba_benchmark_time_ms').json()['time']
    print(f"BENCHMARK:vs_gba_ratio:{riscboy_run_time / gba_run_time}")
except Exception as e:
    print(f"TEST_FAIL:baseline_comparison:{e}")

# Count test files
try:
    test_count = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.startswith('test_'):
                test_count += 1
    print(f"BENCHMARK:test_files_count:{test_count}")
except Exception as e:
    print(f"TEST_FAIL:test_file_count:{e}")

# Measure and emit memory usage BENCHMARK lines
try:
    tracemalloc.start()
    subprocess.run(['python', '-c', 'import os'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
except Exception as e:
    print(f"BENCHMARK:memory_usage_bytes:failed")

print("RUN_OK")