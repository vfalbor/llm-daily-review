import subprocess
import time
import tracemalloc
import pip
import importlib.util
import sys

# Install system package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'cssutils'], check=True)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:cssutils installation failed")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/cssutils/cssutils.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './cssutils'], check=True)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:cssutils installation from source failed")
        sys.exit(0)

# Import the package
start_time = time.time()
spec = importlib.util.find_spec('cssutils')
if spec is None:
    print("INSTALL_FAIL:cssutils import failed")
else:
    print("INSTALL_OK")
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Run a minimal functional test
try:
    import cssutils
    start_time = time.time()
    sheet = cssutils.parseString("body { background-color: #f2f2f2; }")
    end_time = time.time()
    test_time = (end_time - start_time) * 1000
    print(f"TEST_PASS:cssutils_test")
    print(f"BENCHMARK:cssutils_test_ms:{test_time}")
except Exception as e:
    print(f"TEST_FAIL:cssutils_test:{str(e)}")

# Compare performance with similar baseline tool (OWASP)
try:
    import requests
    start_time = time.time()
    requests.get("https://www.owasp.org/")
    end_time = time.time()
    baseline_time = (end_time - start_time) * 1000
    ratio = test_time / baseline_time
    print(f"BENCHMARK:vs_owasp_latency_ratio:{ratio}")
except Exception as e:
    print(f"BENCHMARK:vs_owasp_latency_ratio:Failed to measure")

# Measure memory usage
tracemalloc.start()
start_time = time.time()
import cssutils
sheet = cssutils.parseString("body { background-color: #f2f2f2; }")
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
memory_usage = peak / (1024 * 1024)
print(f"BENCHMARK:memory_usage_mb:{memory_usage}")

# Count lines of code
subprocess.run(['git', 'clone', 'https://github.com/cssutils/cssutils.git'], check=True)
loc_count = int(subprocess.run(['git', 'ls-files', '-z'], cwd='./cssutils', check=True, capture_output=True, text=True).stdout.count('\n'))
print(f"BENCHMARK:loc_count:{loc_count}")

# Print RUN_OK
print("RUN_OK")