import subprocess
import time
import tracemalloc
import sys

# Install system packages with subprocess
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install git")
    print("RUN_OK")
    sys.exit(1)

# Clone and install the hex editor package with subprocess
try:
    subprocess.run(['git', 'clone', 'https://github.com/simonomi/hex-editor.git'], check=True)
    subprocess.run(['pip', 'install', '-e', 'hex-editor'], cwd='hex-editor', check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to clone and install hex editor")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/simonomi/hex-editor.git'], check=True)
        subprocess.run(['pip', 'install', '-e', '.'], cwd='hex-editor', check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install hex editor as fallback")
        print("RUN_OK")
        sys.exit(1)

# Import the hex editor package and measure import time
start_time = time.time()
try:
    import hex_editor
    import_time = time.time() - start_time
    print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
    print("TEST_PASS:import_hex_editor")
except ImportError as e:
    print("TEST_FAIL:import_hex_editor:Failed to import hex editor")
    print(f"BENCHMARK:import_time_ms:NaN")

# Run a minimal functional test with synthetic data
try:
    data = b'\x00\x01\x02\x03\x04\x05\x06\x07'
    start_time = time.time()
    hex_editor.color_code_bytes(data)
    latency = time.time() - start_time
    print(f"BENCHMARK:color_code_latency_ms:{latency*1000:.2f}")
    print("TEST_PASS:color_code_bytes")
except Exception as e:
    print(f"TEST_FAIL:color_code_bytes:{str(e)}")

# Measure memory usage
tracemalloc.start()
hex_editor.color_code_bytes(b'\x00\x01\x02\x03\x04\x05\x06\x07')
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Compare performance vs the most similar baseline tool listed above (Hxd)
try:
    import hxd
    start_time = time.time()
    hxd.color_code_bytes(b'\x00\x01\x02\x03\x04\x05\x06\x07')
    hxd_latency = time.time() - start_time
    ratio = latency / hxd_latency
    print(f"BENCHMARK:vs_hxd_color_code_ratio:{ratio:.2f}")
except ImportError as e:
    print("TEST_SKIP:compare_with_hxd:Failed to import hxd")

# Count lines of code
try:
    loc_count = subprocess.run(['git', 'ls-files', '-z'], check=True, capture_output=True, cwd='hex-editor')
    loc_count = len(loc_count.stdout.decode('utf-8').split('\0'))
    print(f"BENCHMARK:loc_count:{loc_count}")
except subprocess.CalledProcessError as e:
    print("TEST_FAIL:count_loc:Failed to count lines of code")

# Count test files
try:
    test_files_count = subprocess.run(['find', 'tests', '-type', 'f'], check=True, capture_output=True, cwd='hex-editor')
    test_files_count = len(test_files_count.stdout.decode('utf-8').split('\n')) - 1
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except subprocess.CalledProcessError as e:
    print("TEST_FAIL:count_test_files:Failed to count test files")

print("RUN_OK")