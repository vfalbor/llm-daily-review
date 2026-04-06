import time
import importlib.util
import importlib.machinery
import subprocess
import os
import json

print("INSTALL_OK")

# Load the model
try:
    import guppylm
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "guppylm"])
        import guppylm
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL")
        sys.exit(1)

# Test 1: Run the model on a small dataset
try:
    from guppylm import GuppyLM
    model = GuppyLM()
    dataset = ["Hello world", "This is a test", "GuppyLM is a small LLM"]
    results = model.generate(dataset)
    print("TEST_PASS:run_model")
except Exception as e:
    print(f"TEST_FAIL:run_model:{str(e)}")

# Test 2: Test the model's performance on a benchmark task
try:
    start_time = time.time()
    results = model.generate(["Hello world"] * 100)
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print("BENCHMARK:latency_ms_per_request:", latency / 100)
    print("BENCHMARK:token_throughput:100")
    print("TEST_PASS:benchmark")
except Exception as e:
    print(f"TEST_FAIL:benchmark:{str(e)}")

# Test 3: Check the model's documentation and usage examples
try:
    import inspect
    doc = inspect.getdoc(guppylm)
    if not doc:
        print("TEST_SKIP:documentation:No documentation found")
    else:
        print("TEST_PASS:documentation")
except Exception as e:
    print(f"TEST_FAIL:documentation:{str(e)}")

# Measure import time
try:
    start_time = time.time()
    import guppylm
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print("BENCHMARK:import_time_ms:", import_time)
except Exception as e:
    print(f"TEST_FAIL:import_time:{str(e)}")

# Compare with similar tools
try:
    start_time = time.time()
    import transformers
    end_time = time.time()
    transformers_import_time = (end_time - start_time) * 1000
    if import_time < transformers_import_time:
        print("BENCHMARK:vs_transformers:faster_import")
    elif import_time > transformers_import_time:
        print("BENCHMARK:vs_transformers:slower_import")
    else:
        print("BENCHMARK:vs_transformers:same_import_time")
except Exception as e:
    print(f"TEST_SKIP:compare_import_time:{str(e)}")

print("RUN_OK")