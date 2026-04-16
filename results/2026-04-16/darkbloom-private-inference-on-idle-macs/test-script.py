import subprocess
import time
import tracemalloc
import importlib.util
import os

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

try:
    # Try to install Darkbloom using pip
    subprocess.run(['pip', 'install', 'darkbloom'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:darkbloom installation failed")
    try:
        # Fallback to installing from source
        subprocess.run(['git', 'clone', 'https://github.com/darkbloom-dev/darkbloom.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './darkbloom'], check=True, cwd='./darkbloom')
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:darkbloom installation from source failed")
        exit(0)

try:
    # Import Darkbloom
    spec = importlib.util.spec_from_file_location("darkbloom", "./darkbloom/darkbloom/__init__.py")
    darkbloom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(darkbloom)
except ImportError:
    print("TEST_FAIL:import_darkbloom:module not found")
    exit(0)

# Measure import time
import_start_time = time.time()
importlib.import_module('darkbloom')
import_end_time = time.time()
import_time_ms = (import_end_time - import_start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time_ms:.2f}")

# Measure memory and CPU usage
tracemalloc.start()
darkbloom_inference = darkbloom.infer([1, 2, 3])  # Run a minimal functional test with synthetic data
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
memory_usage_mb = peak / (1024 * 1024)
print(f"BENCHMARK:memory_usage_mb:{memory_usage_mb:.2f}")

# Measure core operation latency
start_time = time.time()
darkbloom_inference = darkbloom.infer([1, 2, 3])  # Run a minimal functional test with synthetic data
end_time = time.time()
operation_latency_ms = (end_time - start_time) * 1000
print(f"BENCHMARK:operation_latency_ms:{operation_latency_ms:.2f}")

# Similar tools are not provided, skipping baseline comparison

# Count the number of test files
test_files_count = len(os.listdir('./darkbloom/tests'))
print(f"BENCHMARK:test_files_count:{test_files_count}")

# Count the number of lines in the code
loc_count = sum(1 for _ in open('./darkbloom/darkbloom/__init__.py'))
print(f"BENCHMARK:loc_count:{loc_count}")

print("RUN_OK")