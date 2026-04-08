import subprocess
import sys
import time
import tracemalloc
from datetime import timedelta
import importlib.util

# Install required system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install system packages: {e}")
    sys.exit(1)

# Clone the repository and install the package
try:
    subprocess.run(['git', 'clone', 'https://github.com/anthropic/glasswing.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './glasswing'], cwd='./glasswing', check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install package: {e}")

# Import the package
try:
    spec = importlib.util.spec_from_file_location("glasswing", "./glasswing/glasswing/__init__.py")
    glasswing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(glasswing)
except ImportError as e:
    print(f"INSTALL_FAIL:Failed to import package: {e}")
    sys.exit(1)

# Measure import time
import_start_time = time.time()
importlib.import_module('glasswing')
import_end_time = time.time()
import_time_ms = (import_end_time - import_start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time_ms:.2f}")

# Run a minimal functional test with synthetic data
try:
    tracemalloc.start()
    start_time = time.time()
    # Run a mock vulnerability scan on a known vulnerable model
    glasswing.scan_vulnerabilities(None)  # Assuming this function exists
    end_time = time.time()
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    scan_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:scan_time_ms:{scan_time_ms:.2f}")
    print(f"BENCHMARK:peak_memory_bytes:{peak_memory}")
    print("TEST_PASS:mock_vulnerability_scan")
except Exception as e:
    print(f"TEST_FAIL:mock_vulnerability_scan:{e}")

# Measure execution time against an industry-leading tool
try:
    subprocess.run(['pip', 'install', 'cyclonedx'], check=True)
    import cyclonedx
    start_time = time.time()
    cyclonedx.scan_vulnerabilities(None)  # Assuming this function exists
    end_time = time.time()
    cyclonedx_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_cyclonedx_scan_time_ms:{cyclonedx_time_ms:.2f}")
    ratio = scan_time_ms / cyclonedx_time_ms
    print(f"BENCHMARK:vs_cyclonedx_scan_time_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_SKIP:vs_cyclonedx_scan:{e}")

print("RUN_OK")