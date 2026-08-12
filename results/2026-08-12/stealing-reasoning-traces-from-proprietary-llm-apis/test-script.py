import subprocess
import time
import tracemalloc
import os
import importlib

# Install required APK packages
print("Installing required APK packages...", end="")
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("done")

# Install pip package
try:
    print("Installing stolen-thoughts package...", end="")
    subprocess.run(['pip', 'install', 'stolen-thoughts'], check=False)
    print("done")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")
    try:
        print("Cloning stolen-thoughts repository...", end="")
        subprocess.run(['git', 'clone', 'https://github.com/justinseitz/stolen-thoughts.git'], check=False)
        print("done")
        os.chdir('./stolen-thoughts')
        print("Installing stolen-thoughts package from source...", end="")
        subprocess.run(['pip', 'install', '-e', '.'], check=False)
        print("done")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

# Measure import time
start_time = time.time()
try:
    import stolen_thoughts
    import_time = time.time() - start_time
    print(f"BENCHMARK:import_time_ms:{import_time * 1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_stolen_thoughts:{str(e)}")

# Run a minimal functional test with synthetic data
try:
    print("Running minimal functional test...", end="")
    start_time = time.time()
    tracemalloc.start()
    import stolen_thoughts
    test_data = [1, 2, 3, 4, 5]
    stolen_thoughts_model = stolen_thoughts.StolenThoughtsModel()
    output = stolen_thoughts_model.run(test_data)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    test_time = end_time - start_time
    print("done")
    print(f"BENCHMARK:run_time_ms:{test_time * 1000:.2f}")
    print(f"BENCHMARK:memory_usage_mb:{peak / 1024 / 1024:.2f}")
    print(f"TEST_PASS:run_minimal_functional_test")
except Exception as e:
    print(f"TEST_FAIL:run_minimal_functional_test:{str(e)}")

# Compare output with a baseline model
try:
    print("Comparing output with baseline model...", end="")
    import baseline_model
    baseline_output = baseline_model.run(test_data)
    diff = abs(output - baseline_output)
    print("done")
    print(f"BENCHMARK:output_diff:{diff:.2f}")
    print(f"TEST_PASS:compare_output_with_baseline")
except Exception as e:
    print(f"TEST_FAIL:compare_output_with_baseline:{str(e)}")

# Compare performance with the most similar baseline tool listed above
try:
    print("Comparing performance with LLaMA...", end="")
    import llama
    start_time = time.time()
    llama_model = llama.LLaMA()
    llama_output = llama_model.run(test_data)
    end_time = time.time()
    llama_time = end_time - start_time
    ratio = test_time / llama_time
    print("done")
    print(f"BENCHMARK:vs_llama_run_time_ratio:{ratio:.2f}")
    print(f"TEST_PASS:compare_performance_with_llama")
except Exception as e:
    print(f"TEST_FAIL:compare_performance_with_llama:{str(e)}")

try:
    print(f"BENCHMARK:loc_count:{sum(1 for _ in open('stolen_thoughts/__init__.py').read().splitlines() if _.strip())}")
    print(f"BENCHMARK:test_files_count:{len(os.listdir('tests'))}")
except Exception as e:
    print(f"TEST_FAIL:get_loc_count_and_test_files_count:{str(e)}")

print("RUN_OK")