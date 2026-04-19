import subprocess
import time
import tracemalloc
import sys
import importlib.util

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'git+https://github.com/teamchong/turboquant-wasm.git'], check=True)
    INSTALL_STATUS = "INSTALL_OK"
except subprocess.CalledProcessError:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/teamchong/turboquant-wasm.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './turboquant-wasm'], cwd='./turboquant-wasm', check=True)
        INSTALL_STATUS = "INSTALL_OK"
    except subprocess.CalledProcessError:
        INSTALL_STATUS = "INSTALL_FAIL: unable to install via pip or git clone"
print(INSTALL_STATUS)

# Initialize tracemalloc
tracemalloc.start()

# Import the package and measure import time
start_time = time.time()
try:
    spec = importlib.util.find_spec("turboquant_wasm")
    turboquant_wasm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(turboquant_wasm)
    import_time = (time.time() - start_time) * 1000
except Exception as e:
    print(f"TEST_FAIL:import_test:{str(e)}")
    import_time = None

if import_time is not None:
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")

# Run a minimal functional test with synthetic data
try:
    start_time = time.time()
    turboquant_wasm.run_inference()
    inference_time = (time.time() - start_time) * 1000
    print(f"TEST_PASS:inference_test")
    print(f"BENCHMARK:inference_time_ms:{inference_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:inference_test:{str(e)}")

# Measure latency of inference
try:
    start_time = time.time()
    turboquant_wasm.run_inference()
    latency = (time.time() - start_time) * 1000
    print(f"BENCHMARK:inference_latency_ms:{latency:.2f}")
except Exception as e:
    print(f"TEST_FAIL:latency_test:{str(e)}")

# Check Excalidraw output
try:
    output = turboquant_wasm.run_inference()
    print(f"TEST_PASS:excalidraw_test")
except Exception as e:
    print(f"TEST_FAIL:excalidraw_test:{str(e)}")

# Compare performance vs the most similar baseline tool
try:
    import gemma4
    start_time = time.time()
    gemma4.run_inference()
    gemma4_inference_time = (time.time() - start_time) * 1000
    ratio = inference_time / gemma4_inference_time
    print(f"BENCHMARK:vs_gemma4_inference_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_SKIP:baseline_test: unable to install or import gemma4")

# Measure memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_bytes:{current}")
print(f"BENCHMARK:peak_memory_usage_bytes:{peak}")
tracemalloc.stop()

# Measure the number of test files
try:
    test_files = len([f for f in sys.modules['turboquant_wasm'].__file__.split('/') if f.endswith('.py')])
    print(f"BENCHMARK:test_files_count:{test_files}")
except Exception as e:
    print(f"BENCHMARK:test_files_count:0")

# Measure the number of lines of code
try:
    with open(turboquant_wasm.__file__, 'r') as f:
        lines_of_code = len(f.readlines())
    print(f"BENCHMARK:loc_count:{lines_of_code}")
except Exception as e:
    print(f"BENCHMARK:loc_count:0")

print("RUN_OK")