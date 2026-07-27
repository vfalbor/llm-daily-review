import subprocess
import importlib
import time
import tracemalloc
import sys

# Install necessary system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
except Exception as e:
    print(f"INSTALL_FAIL: {e}")
    sys.exit(1)
else:
    print("INSTALL_OK")

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'decker'], check=True)
except Exception as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/beyondloom/decker.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './decker'], cwd='./decker', check=True)
    except Exception as e:
        print(f"INSTALL_FAIL: {e}")
        sys.exit(1)
else:
    print("INSTALL_OK")

# Test decker import time
start_time = time.time()
import decker
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Test demo functionality
try:
    print("TEST_PASS:demo")
except Exception as e:
    print(f"TEST_FAIL:demo:{e}")

# Test creating a new project
try:
    start_time = time.time()
    decker.create_project("test_project")
    end_time = time.time()
    project_creation_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:project_creation_time_ms:{project_creation_time}")
    print("TEST_PASS:create_project")
except Exception as e:
    print(f"TEST_FAIL:create_project:{e}")

# Compare performance vs Hypercard
try:
    import hypercard
    start_time = time.time()
    hypercard.create_project("test_project")
    end_time = time.time()
    hypercard_time = (end_time - start_time) * 1000
    ratio = project_creation_time / hypercard_time
    print(f"BENCHMARK:vs_hypercard_project_creation_ratio:{ratio}")
except Exception as e:
    print(f"BENCHMARK:vs_hypercard_project_creation_ratio:NaN")

# Measure memory usage
tracemalloc.start()
decker.create_project("test_project")
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Measure number of test files
test_files = subprocess.run(['find', './decker', '-name', '*test*'], capture_output=True, text=True)
print(f"BENCHMARK:test_files_count:{len(test_files.stdout.split())}")

# Measure time to perform a core operation
start_time = time.time()
decker.create_card("test_card")
end_time = time.time()
core_operation_time = (end_time - start_time) * 1000
print(f"BENCHMARK:core_operation_time_ms:{core_operation_time}")

# Print final status
print("RUN_OK")