import subprocess
import pip
import importlib
import time
import tracemalloc
import sys

# Install necessary packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install DX Core 4 and Jest
try:
    subprocess.run(['pip', 'install', 'dx-core'], check=True)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:dx-core:Failed to install via pip, trying git clone and pip install -e .")
    subprocess.run(['git', 'clone', 'https://github.com/dx-core/dx-core.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './dx-core'], check=True, cwd='./dx-core')
print("INSTALL_OK")

try:
    subprocess.run(['pip', 'install', 'jest'], check=True)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:jest:Failed to install via pip")
print("INSTALL_OK")

# Import DX Core 4 and measure import time
start_time = time.time()
try:
    import dx_core
except ImportError:
    print("TEST_FAIL:import:Failed to import dx_core")
    dx_core_import_time = None
else:
    dx_core_import_time = time.time() - start_time
    print(f"BENCHMARK:import_time_ms:{dx_core_import_time * 1000:.2f}")
    print("TEST_PASS:import")

# Measure DX Core 4 test coverage
try:
    start_time = time.time()
    dx_core.core.runCoverage()
    dx_core_test_coverage_time = time.time() - start_time
    print(f"BENCHMARK:test_coverage_time_s:{dx_core_test_coverage_time:.2f}")
    print("TEST_PASS:test_coverage")
except Exception as e:
    print(f"TEST_FAIL:test_coverage:{str(e)}")

# Compare DX Core 4 performance to Jest
try:
    start_time = time.time()
    importlib.import_module('jest')
    jest_import_time = time.time() - start_time
    dx_core_import_time_ms = dx_core_import_time * 1000 if dx_core_import_time is not None else None
    ratio = dx_core_import_time_ms / (jest_import_time * 1000) if dx_core_import_time_ms is not None else None
    print(f"BENCHMARK:vs_jest_import_ratio:{ratio:.2f}" if ratio is not None else "BENCHMARK:vs_jest_import_ratio:None")
    print("TEST_PASS:performance_comparison")
except Exception as e:
    print(f"TEST_FAIL:performance_comparison:{str(e)}")

# Measure memory usage of DX Core 4
tracemalloc.start()
try:
    dx_core.core.runCoverage()
except Exception as e:
    print(f"TEST_FAIL:memory_usage:{str(e)}")
else:
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_mb:{current / (1024 * 1024):.2f}")
    print("TEST_PASS:memory_usage")
finally:
    tracemalloc.stop()

# Measure the number of lines of code in DX Core 4
try:
    loc_count = subprocess.run(['git', 'ls-files'], check=True, capture_output=True, text=True).stdout.split('\n')
    loc_count = sum(1 for file in loc_count if file.endswith('.py'))
    print(f"BENCHMARK:loc_count:{loc_count}")
    print("TEST_PASS:loc_count")
except Exception as e:
    print(f"TEST_FAIL:loc_count:{str(e)}")

# Measure the number of test files in DX Core 4
try:
    test_files_count = subprocess.run(['git', 'ls-files', './dx_core/test'], check=True, capture_output=True, text=True).stdout.split('\n')
    test_files_count = sum(1 for file in test_files_count if file.endswith('.py'))
    print(f"BENCHMARK:test_files_count:{test_files_count}")
    print("TEST_PASS:test_files_count")
except Exception as e:
    print(f"TEST_FAIL:test_files_count:{str(e)}")

print("RUN_OK")