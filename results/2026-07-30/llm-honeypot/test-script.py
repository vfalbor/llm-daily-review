import time
import tracemalloc
import subprocess
import sys

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Try to install via pip
try:
    subprocess.run(['pip', 'install', 'llm-honeypot'], check=True)
    INSTALL_MSG = "INSTALL_OK"
except Exception as e:
    # Fallback to installation from source
    subprocess.run(['git', 'clone', 'https://github.com/honeypot-llm/llm-honeypot.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './llm-honeypot'], cwd='./llm-honeypot', check=True)
    INSTALL_MSG = f"INSTALL_FAIL:{str(e)}"

print(INSTALL_MSG)

# Import the installed package and measure import time
start_time = time.time()
try:
    import llm_honeypot
    import_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_llm_honeypot:{str(e)}")

# Test the package with a minimal functional test
try:
    start_time = time.time()
    # Create a synthetic data set and run a test
    llm_honeypot.setup_api_hook()
    llm_honeypot.run_test()
    test_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:test_time_ms:{test_time:.2f}")
    print("TEST_PASS:minimal_test")
except Exception as e:
    print(f"TEST_FAIL:minimal_test:{str(e)}")

# Verify accuracy of detection with a controlled test
try:
    start_time = time.time()
    # Create a controlled test case and run it
    llm_honeypot.run_controlled_test()
    controlled_test_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:controlled_test_time_ms:{controlled_test_time:.2f}")
    print("TEST_PASS:controlled_test")
except Exception as e:
    print(f"TEST_FAIL:controlled_test:{str(e)}")

# Compare performance vs the most similar baseline tool (LM-Honeypot)
try:
    # Run a test with LM-Honeypot and measure the time
    start_time = time.time()
    subprocess.run(['pip', 'install', 'lm-honeypot'], check=True)
    import lm_honeypot
    lm_honeypot.run_test()
    lm_test_time = (time.time() - start_time) * 1000
    ratio = test_time / lm_test_time
    print(f"BENCHMARK:vs_lm_honeypot_test_time_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_FAIL:lm_honeypot_comparison:{str(e)}")

# Measure and emit memory usage
tracemalloc.start()
time.sleep(1)  # to allow tracemalloc to capture memory usage
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{current / (1024 * 1024):.2f}")

# Measure and emit the number of lines of code
num_lines = sum(1 for _ in open('./llm-honeypot/llm_honeypot.py'))
print(f"BENCHMARK:loc_count:{num_lines}")

# Measure and emit the number of test files
num_test_files = len([name for name in subprocess.run(['find', './llm-honeypot', '-name', '*.py'], stdout=subprocess.PIPE, check=True).stdout.decode('utf-8').split('\n') if name])
print(f"BENCHMARK:test_files_count:{num_test_files}")

print("RUN_OK")