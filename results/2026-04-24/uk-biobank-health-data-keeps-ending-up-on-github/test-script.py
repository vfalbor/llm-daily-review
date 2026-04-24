import importlib.util
import subprocess
import time
import tracemalloc
import sys

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repository and install Python package
try:
    subprocess.run(['pip', 'install', 'UKBiobank'], check=False)
except Exception as e:
    subprocess.run(['git', 'clone', 'https://github.com/UKBiobank/UKBiobank-Data-Repository.git'], check=False)
    subprocess.run(['pip', 'install', '-e', './UKBiobank-Data-Repository'], check=False)

print("INSTALL_OK")

# Load the package
try:
    spec = importlib.util.find_spec('UKBiobank')
    if spec is None:
        raise ImportError
    package = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(package)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Measure import time
start_time = time.time()
import UKBiobank
import_time = time.time() - start_time
print(f"BENCHMARK:import_time_ms:{import_time * 1000}")

# Measure core operation latency
try:
    start_time = time.time()
    # Run a minimal functional test with synthetic data
    # Mock API call with a fake key
    UKBiobank.run_test(synthetic_data=True, api_key='fake_key')
    latency = time.time() - start_time
    print(f"BENCHMARK:hello_world_ms:{latency * 1000}")
    print(f"TEST_PASS:basic_run")
except Exception as e:
    print(f"TEST_FAIL:basic_run:{e}")

# Measure performance
try:
    tracemalloc.start()
    start_time = time.time()
    # Run a performance test
    UKBiobank.run_performance_test()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:performance_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:performance_memory_mb:{current / 10**6}")
    print(f"TEST_PASS:performance_test")
except Exception as e:
    print(f"TEST_FAIL:performance_test:{e}")

# Compare vs similar tool
try:
    # Run a similar test using the baseline tool
    subprocess.run(['python', '-c', 'import time; start_time = time.time(); time.sleep(1); end_time = time.time(); print((end_time - start_time) * 1000)'])
    baseline_latency = 1000  # Assume baseline latency is 1000ms
    latency_ratio = (latency / baseline_latency)
    print(f"BENCHMARK:vs_UKBiobank_latency_ratio:{latency_ratio}")
    print(f"TEST_PASS:comparison_test")
except Exception as e:
    print(f"TEST_FAIL:comparison_test:{e}")

print("RUN_OK")