import subprocess
import time
import tracemalloc
import os

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'gcc', 'make', 'libffi-dev'], check=False)

# Clone QuadRF repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/geerlingguy/quadrf'], check=True)
    INSTALL_OK = True
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:git clone failed with error {e}")
    INSTALL_OK = False

# Change directory to QuadRF
os.chdir('quadrf')

# Build and install QuadRF tool
try:
    start_time = time.time()
    subprocess.run(['make'], check=True)
    install_time = time.time() - start_time
    print(f"BENCHMARK:install_time_s:{install_time:.2f}")
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:make failed with error {e}")

# Count source files
try:
    file_count = len([name for name in os.listdir('.') if os.path.isfile(name)])
    print(f"BENCHMARK:source_file_count:{file_count}")
except Exception as e:
    print(f"TEST_FAIL:count_source_files:{e}")

# Scan for WiFi signals
try:
    start_time = time.time()
    subprocess.run(['./quadrf', '-s'], check=True)
    scan_time = time.time() - start_time
    print(f"BENCHMARK:scan_time_ms:{scan_time*1000:.2f}")
    print("TEST_PASS:scan_wifi_signals")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:scan_wifi_signals:{e}")
except Exception as e:
    print(f"TEST_FAIL:scan_wifi_signals:{e}")

#Decode and parse signal data
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['./quadrf', '-d'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    decode_time = time.time() - start_time
    print(f"BENCHMARK:decode_time_ms:{decode_time*1000:.2f}")
    print(f"BENCHMARK:decode_memory_mb:{peak/1024/1024:.2f}")
    print("TEST_PASS:decode_signal_data")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:decode_signal_data:{e}")
except Exception as e:
    print(f"TEST_FAIL:decode_signal_data:{e}")

# Compare performance vs NetworkMiner (assumed baseline tool)
try:
    # Run NetworkMiner example
    start_time = time.time()
    subprocess.run(['networkminer', '-e'], check=True)
    baseline_time = time.time() - start_time

    # Calculate ratio
    ratio = scan_time / baseline_time
    print(f"BENCHMARK:vs_networkminer_scan_ratio:{ratio:.2f}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:run_networkminer_example:{e}")
except Exception as e:
    print(f"TEST_FAIL:run_networkminer_example:{e}")

print("RUN_OK")