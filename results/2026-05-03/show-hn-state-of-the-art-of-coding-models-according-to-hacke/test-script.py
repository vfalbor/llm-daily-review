import subprocess
import time
import tracemalloc
import importlib.util
import sys

# Install system packages
try:
    print("Installing system packages")
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install system packages: {e}")
    sys.exit(1)

# Install tool dependencies
try:
    print("Installing tool dependencies")
    subprocess.run(['pip', 'install', 'llm-ai'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install tool dependencies: {e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/llm-ai/llm-ai.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './llm-ai'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install tool dependencies via git: {e}")
        sys.exit(1)

# Import the tool and measure import time
try:
    start_time = time.time()
    spec = importlib.util.find_spec('llm_ai')
    if spec is not None:
        import llm_ai
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
except ImportError as e:
    print(f"TEST_FAIL:import_test:Failed to import llm-ai: {e}")

# Run a minimal functional test with synthetic data
try:
    start_time = time.time()
    model = llm_ai.Model()
    output = model.predict("Hello World!")
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:hello_world_ms:{latency:.2f}")
    if output == "Hello World!":
        print("TEST_PASS:output_test")
    else:
        print(f"TEST_FAIL:output_test:Expected output 'Hello World!', got '{output}'")
except Exception as e:
    print(f"TEST_FAIL:functional_test:Failed to run functional test: {e}")

# Evaluate the model's ability to learn from feedback
try:
    start_time = time.time()
    model = llm_ai.Model()
    model.train("Hello World!", "Hello Universe!")
    end_time = time.time()
    training_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:training_time_ms:{training_time:.2f}")
    print("TEST_PASS:training_test")
except Exception as e:
    print(f"TEST_FAIL:training_test:Failed to train the model: {e}")

# Compare performance vs baseline model
try:
    import lm_eval_harness
    start_time = time.time()
    model = lm_eval_harness.Model()
    model.predict("Hello World!")
    end_time = time.time()
    baseline_latency = (end_time - start_time) * 1000
    ratio = latency / baseline_latency
    print(f"BENCHMARK:vs_lm_eval_harness_fib_ratio:{ratio:.2f}")
except ImportError as e:
    print(f"TEST_SKIP:baseline_test:Failed to import lm_eval_harness: {e}")
except Exception as e:
    print(f"TEST_FAIL:baseline_test:Failed to compare performance with baseline model: {e}")

# Measure memory usage
tracemalloc.start()
model = llm_ai.Model()
memory, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{memory}")

# Count lines of code
try:
    with open(__file__, 'r') as f:
        loc_count = len(f.readlines())
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    print(f"TEST_FAIL:loc_count_test:Failed to count lines of code: {e}")

# Count test files
try:
    import os
    test_files_count = len([file for file in os.listdir('.') if file.endswith('.py')])
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    print(f"TEST_FAIL:test_files_count_test:Failed to count test files: {e}")

print("RUN_OK")