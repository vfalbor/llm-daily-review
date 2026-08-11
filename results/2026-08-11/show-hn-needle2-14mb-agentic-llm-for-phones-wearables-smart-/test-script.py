import subprocess
import time
import tracemalloc
import sys

# Install required system packages
print("Installing required system packages...")
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Install Needle2 via pip
print("Installing Needle2 via pip...")
try:
    subprocess.run(['pip', 'install', 'needle'], check=True)
    print("INSTALL_OK")
except Exception as e:
    # Fallback to git clone and pip install -e
    print("INSTALL_FAIL: pip install failed, falling back to git clone and pip install -e...")
    subprocess.run(['git', 'clone', 'https://github.com/cactuscompute/needle.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './needle'], check=True, cwd='./needle')
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Import Needle2 and measure import time
print("Importing Needle2 and measuring import time...")
start_time = time.time()
try:
    import needle
    import_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
    print("TEST_PASS:import_needle")
except Exception as e:
    print(f"TEST_FAIL:import_needle:{e}")

# Run a minimal functional test with synthetic data
print("Running a minimal functional test with synthetic data...")
start_time = time.time()
try:
    tracemalloc.start()
    model = needle.load_model()
    result = model.predict("This is a test sentence.")
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:predict_latency_ms:{latency:.2f}")
    print(f"BENCHMARK:predict_memory_mb:{peak / 10**6:.2f}")
    print("TEST_PASS:predict_test")
except Exception as e:
    print(f"TEST_FAIL:predict_test:{e}")

# Compare with large LLMs for similar tasks
print("Comparing with large LLMs for similar tasks...")
try:
    # Load T5 model for comparison
    import transformers
    t5_model = transformers.T5ForConditionalGeneration.from_pretrained("t5-small")
    t5_tokenizer = transformers.T5Tokenizer.from_pretrained("t5-small")
    t5_input = t5_tokenizer.encode("This is a test sentence.", return_tensors="pt")
    start_time = time.time()
    t5_output = t5_model.generate(t5_input)
    end_time = time.time()
    t5_latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_t5_predict_latency_ms:{t5_latency:.2f}")
    print(f"BENCHMARK:vs_t5_predict_latency_ratio:{latency / t5_latency:.2f}")
    print("TEST_PASS:compare_with_t5")
except Exception as e:
    print(f"TEST_FAIL:compare_with_t5:{e}")

# Measure time/memory/count benchmarks
print("Measuring time/memory/count benchmarks...")
start_time = time.time()
try:
    model = needle.load_model()
    end_time = time.time()
    load_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:load_time_ms:{load_time:.2f}")
    print(f"BENCHMARK:loc_count:{len(open(__file__).readlines())}")
    print(f"BENCHMARK:test_files_count:{len([name for name in sys.modules if name.startswith('test_')])}")
    print("TEST_PASS:benchmark_tests")
except Exception as e:
    print(f"TEST_FAIL:benchmark_tests:{e}")

print("RUN_OK")