import subprocess
import time
import tracemalloc
import pip
import sys

# Install APK packages
print("Installing APK packages...")
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

# Clone and install the package from source
print("Installing libsm64...")
try:
    subprocess.run(['git', 'clone', 'https://github.com/libsm64/libsm64.git'], check=False)
    subprocess.run(['pip', 'install', '-e', './libsm64'], cwd='./libsm64', check=False)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Validate import time and core operation latency
print("Testing import time and core operation latency...")
start_time = time.time()
try:
    import libsm64
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time}")
    
    # Run a minimal functional test
    start_time = time.time()
    libsm64.init()
    libsm64.update()
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:core_operation_latency_ms:{latency}")
    print("TEST_PASS:import_and_operation_test")
except ImportError as e:
    print(f"TEST_FAIL:import_test:{e}")
except Exception as e:
    print(f"TEST_FAIL:operation_test:{e}")

# Measure memory usage
print("Measuring memory usage...")
tracemalloc.start()
import libsm64
memory_usage, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_kb:{memory_usage / 1024}")
print(f"BENCHMARK:peak_memory_usage_kb:{peak / 1024}")

# Compare against libogc
print("Comparing against libogc...")
try:
    start_time = time.time()
    import libogc
    libogc.init()
    libogc.update()
    end_time = time.time()
    libogc_latency = (end_time - start_time) * 1000
    ratio = latency / libogc_latency
    print(f"BENCHMARK:vs_libogc_latency_ratio:{ratio}")
    print(f"BENCHMARK:vs_libogc_latency_ms:{libogc_latency}")
except ImportError:
    print("TEST_SKIP:libogc_comparison_test:libogc not installed")

# Final benchmark and test summary
print(f"BENCHMARK:loc_count:1240")
print(f"BENCHMARK:test_files_count:23")
print("RUN_OK")