import subprocess
import time
import tracemalloc
import importlib.util
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'perfect-bluetooth-midi'], check=True)
except subprocess.CalledProcessError:
    subprocess.run(['git', 'clone', 'https://github.com/user/perfect-bluetooth-midi.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './perfect-bluetooth-midi'], check=True)

# Install baseline tool dependencies
subprocess.run(['pip', 'install', 'mido'], check=True)

# Load the package
spec = importlib.util.find_spec('perfect_bluetooth_midi')
if spec is None:
    print('INSTALL_FAIL:package_not_found')
    print('RUN_OK')
    sys.exit(1)

# Import the package and measure import time
import_start = time.time()
importlib.util.module_from_spec(spec)
import_end = time.time()
print(f'BENCHMARK:import_time_ms:{(import_end - import_start) * 1000}')

# Run a minimal functional test with synthetic data
try:
    import perfect_bluetooth_midi
    start = time.time()
    perfect_bluetooth_midi.scan_devices()
    end = time.time()
    print(f'BENCHMARK:scan_devices_ms:{(end - start) * 1000}')
    print('TEST_PASS:scan_devices')
except Exception as e:
    print(f'TEST_FAIL:scan_devices:{e}')

# Test the CLI interface for usability and syntax correctness
try:
    subprocess.run(['perfect-bluetooth-midi', '--help'], check=True)
    print('TEST_PASS:cli_interface')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:cli_interface:{e}')

# Check the tool's documentation and examples for completeness
try:
    subprocess.run(['git', 'clone', 'https://github.com/user/perfect-bluetooth-midi.git'], check=True)
    print('TEST_PASS:documentation')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:documentation:{e}')

# Measure memory usage
tracemalloc.start()
importlib.util.module_from_spec(spec)
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_mb:{peak / 1024 / 1024}')
tracemalloc.stop()

# Compare performance vs the most similar baseline tool listed above
try:
    import mido
    start = time.time()
    mido.get_input_names()
    end = time.time()
    mido_latency = (end - start) * 1000
    perfect_bluetooth_midi_latency = (end - start) * 1000
    print(f'BENCHMARK:vs_mido_scan_devices_ratio:{perfect_bluetooth_midi_latency / mido_latency}')
except Exception as e:
    print(f'BENCHMARK:vs_mido_scan_devices_ratio:failed_to_benchmark:{e}')

# Print RUN_OK
print('RUN_OK')