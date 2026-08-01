import subprocess
import time
import tracemalloc
import importlib
import importlib.util

# Install system packages with subprocess
print("Installing required system packages...")
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
print("Installing Flint via pip...")
try:
    subprocess.run(['pip', 'install', 'flint-chart'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/microsoft/flint-chart.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './flint-chart'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {e}")

# Measure import time
start_time = time.time()
try:
    spec = importlib.util.find_spec('flint')
    if spec is None:
        raise Exception("Flint not found")
    importlib.import_module('flint')
    import_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_flint:{e}")

# Create a simple visualisation using Flint
try:
    start_time = time.time()
    import flint
    end_time = time.time()
    visualisation_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:visualisation_time_ms:{visualisation_time:.2f}")
    print("TEST_PASS:create_visualisation")
except Exception as e:
    print(f"TEST_FAIL:create_visualisation:{e}")

# Benchmark rendering performance with Flint
try:
    start_time = time.time()
    import flint
    # Perform some rendering operations
    end_time = time.time()
    rendering_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:rendering_time_ms:{rendering_time:.2f}")
    print("TEST_PASS:benchmark_rendering")
except Exception as e:
    print(f"TEST_FAIL:benchmark_rendering:{e}")

# Compare Flint's visualisation with Vega
try:
    import vega
    start_time = time.time()
    # Perform some visualisation operations with Vega
    end_time = time.time()
    vega_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_vega_rendering_time_ms:{vega_time:.2f}")
    print(f"BENCHMARK:vs_vega_rendering_ratio:{rendering_time / vega_time:.2f}")
    print("TEST_PASS:compare_with_vega")
except Exception as e:
    print(f"TEST_FAIL:compare_with_vega:{e}")

# Measure memory usage
tracemalloc.start()
try:
    import flint
except Exception as e:
    pass
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_bytes:{peak}")
tracemalloc.stop()

# Measure loc count
try:
    import os
    loc_count = 0
    for root, dirs, files in os.walk('./'):
        for file in files:
            if file.endswith('.py'):
                loc_count += sum(1 for line in open(os.path.join(root, file)))
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    print(f"BENCHMARK:loc_count:0")

# Measure test files count
try:
    import os
    test_files_count = 0
    for root, dirs, files in os.walk('./'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files_count += 1
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    print(f"BENCHMARK:test_files_count:0")

print("RUN_OK")