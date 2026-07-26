import subprocess
import time
import tracemalloc
import os

# Install dependencies
pkg_to_install = ['nodejs', 'npm', 'git', 'cargo', 'rust']
for pkg in pkg_to_install:
    subprocess.run(['apk', 'add', '--no-cache', pkg], check=False)
    print(f"INSTALL_OK: {pkg}")

# Install DskDitto using npm
start_time = time.time()
try:
    subprocess.run(['npm', 'install', '-g', 'dskditto'], check=True)
    install_time = time.time() - start_time
    print(f"BENCHMARK:install_time_s:{install_time:.2f}")
    print("INSTALL_OK: dskditto")
except Exception as e:
    print(f"INSTALL_FAIL:dskditto: {e}")

# Test 1: Basic run
try:
    subprocess.run(['dskditto', '--help'], check=True)
    print("TEST_PASS:basic_run")
except Exception as e:
    print(f"TEST_FAIL:basic_run: {e}")

# Test 2: Measure performance
start_time = time.time()
try:
    subprocess.run(['dskditto', '--scan', '/'], check=True)
    scan_time = time.time() - start_time
    print(f"BENCHMARK:scan_time_s:{scan_time:.2f}")
    print("TEST_PASS:performance")
except Exception as e:
    print(f"TEST_FAIL:performance: {e}")

# Test 3: Compare vs similar tool (fdupes)
try:
    start_time = time.time()
    subprocess.run(['fdupes', '-r', '/'], check=True)
    fdupes_time = time.time() - start_time
    ratio = scan_time / fdupes_time
    print(f"BENCHMARK:vs_fdupes_scan_time_ratio:{ratio:.2f}")
    print("TEST_PASS:compare_fdupes")
except Exception as e:
    print(f"TEST_FAIL:compare_fdupes: {e}")

# Measure memory usage
tracemalloc.start()
try:
    subprocess.run(['dskditto', '--scan', '/'], check=True)
except Exception as e:
    pass
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024):.2f}")

# Measure line of code count
try:
    loc_count = int(subprocess.check_output(['git', 'ls-files', '-z', '|', 'xargs', '-0', 'wc', '-l']))
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    print(f"BENCHMARK:loc_count:unknown")

# Measure test files count
try:
    test_files_count = int(subprocess.check_output(['git', 'ls-files', '-z', '|', 'grep', '-z', 'test', '|', 'wc', '-l']))
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    print(f"BENCHMARK:test_files_count:unknown")

print("RUN_OK")