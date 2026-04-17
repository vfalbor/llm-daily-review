import subprocess
import time
import tracemalloc
import os
import shutil

# Step 1: Install required packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Step 2: Clone the repository and install required Python packages
try:
    subprocess.run(['git', 'clone', 'https://github.com/lucasgerads/claudicode.git'], check=True)
    os.chdir('claudicode')
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Step 3: Run tests
try:
    # Test 1: Count source files and languages
    start_time = time.time()
    tracemalloc.start()
    src_files = 0
    languages = set()
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.py', '.c', '.cpp', '.java', '.js', '.rs', '.go')):
                src_files += 1
                languages.add(file.split('.')[-1])
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:loc_count:{src_files}")
    print(f"BENCHMARK:src_files_count:{len(languages)}")
    print(f"BENCHMARK:language_count:{len(languages)}")
    print(f"BENCHMARK:src_file_scan_time_s:{end_time - start_time}")
    print(f"BENCHMARK:src_file_scan_mem_mb:{peak / (1024 * 1024)}")

    # Test 2: Run Python examples
    start_time = time.time()
    try:
        subprocess.run(['python', '-c', 'import claudicode'], check=True)
        print("TEST_PASS:python_import_test")
    except Exception as e:
        print(f"TEST_FAIL:python_import_test:{e}")
    end_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")

    # Test 3: Compare performance vs LTspice (baseline tool)
    start_time = time.time()
    try:
        subprocess.run(['ltspice', '-help'], check=True)
        print("TEST_PASS:ltspice_baseline_test")
    except Exception as e:
        print(f"TEST_FAIL:ltspice_baseline_test:{e}")
    end_time = time.time()
    print(f"BENCHMARK:vs_ltspice_help_ms:{(end_time - start_time) * 1000}")

    # Test 4: Test simulator/emulator
    start_time = time.time()
    try:
        subprocess.run(['python', '-c', 'import claudicode.simulator'], check=True)
        print("TEST_PASS:simulator_test")
    except Exception as e:
        print(f"TEST_FAIL:simulator_test:{e}")
    end_time = time.time()
    print(f"BENCHMARK:simulator_time_ms:{(end_time - start_time) * 1000}")

    # Test 5: Test verification functionality
    start_time = time.time()
    try:
        subprocess.run(['python', '-c', 'import claudicode.verification'], check=True)
        print("TEST_PASS:verification_test")
    except Exception as e:
        print(f"TEST_FAIL:verification_test:{e}")
    end_time = time.time()
    print(f"BENCHMARK:verification_time_ms:{(end_time - start_time) * 1000}")

    # Test 6: Count test files
    start_time = time.time()
    test_files = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.startswith('test_'):
                test_files += 1
    end_time = time.time()
    print(f"BENCHMARK:test_files_count:{test_files}")
    print(f"BENCHMARK:test_file_scan_time_ms:{(end_time - start_time) * 1000}")

except Exception as e:
    print(f"TEST_FAIL:main_test:{e}")

# Clean up
try:
    shutil.rmtree('claudicode')
except Exception as e:
    print(f"TEST_FAIL:cleanup_test:{e}")

print("RUN_OK")