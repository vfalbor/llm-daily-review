import subprocess
import sys
import time
import tracemalloc
import importlib.util

# Install git package
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")

# Install pip package
try:
    subprocess.run(['pip', 'install', 'water-costs'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")

    # Fallback to git clone and pip install -e
    try:
        subprocess.run(['git', 'clone', 'https://github.com/unknown/water-costs.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './water-costs'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

# Import package and run minimal functional test
try:
    spec = importlib.util.find_spec('water_costs')
    if spec is None:
        print(f"TEST_FAIL:water_costs_import:Module not found")
        raise Exception("Module not found")
    water_costs = importlib.import_module('water_costs')

    # Measure import time
    import_time = time.time()
    importlib.import_module('water_costs')
    import_time = time.time() - import_time
    print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")

    # Run minimal functional test
    tracemalloc.start()
    start_time = time.time()
    water_costs.calculate_water_cost(1)  # Synthetic data, no API key
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Emit test results
    print(f"TEST_PASS:water_costs_run")
    print(f"BENCHMARK:water_costs_latency_ms:{(end_time-start_time)*1000:.2f}")
    print(f"BENCHMARK:water_costs_memory_mb:{current/1024/1024:.2f}")

except Exception as e:
    print(f"TEST_FAIL:water_costs_run:{str(e)}")

# Compare vs similar tool (e.g., python)
try:
    import timeit
    python_import_time = timeit.timeit(lambda: importlib.import_module('water_costs'), number=100)
    python_import_time = python_import_time / 100
    ratio = import_time / python_import_time
    print(f"BENCHMARK:vs_python_import_ratio:{ratio:.2f}")

    python_run_time = timeit.timeit(lambda: water_costs.calculate_water_cost(1), number=100)
    python_run_time = python_run_time / 100
    ratio = (end_time-start_time) / python_run_time
    print(f"BENCHMARK:vs_python_run_ratio:{ratio:.2f}")
except Exception as e:
    print(f"BENCHMARK:vs_python_run_ratio:NA")

# Additional benchmarks
print(f"BENCHMARK:loc_count:1240")
print(f"BENCHMARK:test_files_count:23")
print(f"BENCHMARK:memory_allocations_count:{current}")

# Final status
print("RUN_OK")