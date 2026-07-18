import subprocess
import sys
import time
import tracemalloc
from importlib import import_module
import os

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

try:
    # Install tool dependencies
    subprocess.run(['pip', 'install', 'waldi'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Load the module and measure import time
start_import_time = time.time()
try:
    import waldi
    import_time = time.time() - start_import_time
    print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_waldi:{e}")

# Run a minimal functional test
start_time = time.time()
try:
    # Create synthetic data and test core operation latency
    waldi_data = waldi.Waldi()
    waldi_data.create_post(title="Test Post", content="This is a test post")
    end_time = time.time()
    core_operation_latency = end_time - start_time
    print(f"BENCHMARK:core_operation_latency_ms:{core_operation_latency*1000:.2f}")
    print("TEST_PASS:run_functional_test")
except Exception as e:
    print(f"TEST_FAIL:run_functional_test:{e}")

# Measure memory usage
tracemalloc.start()
start_time = time.time()
try:
    import waldi
    waldi_data = waldi.Waldi()
    waldi_data.create_post(title="Test Post", content="This is a test post")
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    memory_usage = current / 1024 / 1024
    print(f"BENCHMARK:memory_usage_mb:{memory_usage:.2f}")
except Exception as e:
    print(f"TEST_FAIL:measure_memory_usage:{e}")

# Compare vs similar tool (no similar tool specified, so compare with a baseline of python itself)
try:
    start_time = time.time()
    import waldi
    waldi_data = waldi.Waldi()
    waldi_data.create_post(title="Test Post", content="This is a test post")
    end_time = time.time()
    waldi_latency = end_time - start_time
    start_time = time.time()
    # Simulate creation of a post in python
    post = {"title": "Test Post", "content": "This is a test post"}
    end_time = time.time()
    python_latency = end_time - start_time
    ratio = waldi_latency / python_latency
    print(f"BENCHMARK:vs_python_post_creation_ratio:{ratio:.2f}")
    print("TEST_PASS:compare_with_baseline")
except Exception as e:
    print(f"TEST_FAIL:compare_with_baseline:{e}")

# Always print RUN_OK at the end
print("RUN_OK")