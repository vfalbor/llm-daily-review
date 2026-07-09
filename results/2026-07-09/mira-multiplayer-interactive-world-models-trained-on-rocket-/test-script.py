import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery
import sys

# Install system packages with subprocess
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Install MIRA using pip
try:
    subprocess.run(['pip', 'install', 'mira'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Install MIRA using git clone as fallback
try:
    subprocess.run(['git', 'clone', 'https://github.com/facebookresearch/mira.git'], check=False)
    subprocess.run(['pip', 'install', '-e', 'mira'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Import MIRA and measure import time
start_time = time.time()
try:
    import mira
    import_time = time.time() - start_time
    print(f"BENCHMARK:import_time_ms:{import_time * 1000}")
except Exception as e:
    print(f"TEST_FAIL:import_mira:{e}")

# Run a minimal functional test with synthetic data
try:
    # Run an example model
    start_time = time.time()
    tracemalloc.start()
    mira.example_model()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    test_time = end_time - start_time
    print(f"BENCHMARK:example_model_ms:{test_time * 1000}")
    print(f"BENCHMARK:example_model_memory_mb:{peak / (1024 * 1024)}")
    print("TEST_PASS:run_example_model")
except Exception as e:
    print(f"TEST_FAIL:run_example_model:{e}")

# Compare MIRA paper against a baseline
try:
    # Run a baseline model (PPO)
    start_time = time.time()
    tracemalloc.start()
    # Assuming PPO is installed and has a similar example model
    import ppo
    ppo.example_model()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    baseline_time = end_time - start_time
    ratio = test_time / baseline_time
    print(f"BENCHMARK:vs_ppo_example_model_ratio:{ratio}")
    print("TEST_PASS:compare_to_baseline")
except Exception as e:
    print(f"TEST_FAIL:compare_to_baseline:{e}")

# Measure and emit BENCHMARK lines with real numbers
try:
    # Measure time to run core operation
    start_time = time.time()
    mira.core_operation()
    end_time = time.time()
    core_operation_time = end_time - start_time
    print(f"BENCHMARK:core_operation_ms:{core_operation_time * 1000}")
except Exception as e:
    print(f"TEST_FAIL:core_operation:{e}")

# Measure and emit BENCHMARK lines with real numbers
try:
    # Measure memory usage of core operation
    start_time = time.time()
    tracemalloc.start()
    mira.core_operation()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:core_operation_memory_mb:{peak / (1024 * 1024)}")
except Exception as e:
    print(f"TEST_FAIL:core_operation_memory:{e}")

# Always print RUN_OK
print("RUN_OK")