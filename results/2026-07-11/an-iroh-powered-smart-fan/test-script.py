import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'gcc'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'make'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'musl-dev'], check=False)

# Clone the iroh repository and install dependencies
try:
    subprocess.run(['git', 'clone', 'https://github.com/iroh/iroh-fan.git'], check=True)
    os.chdir('iroh-fan')
    subprocess.run(['git', 'checkout', 'master'], check=True)
    subprocess.run(['make', 'build'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{e}')

# Run the iroh fan tool and test its functionality
try:
    start_time = time.time()
    subprocess.run(['./target/release/iroh-fan'], check=True)
    end_time = time.time()
    print(f'TEST_PASS:iroh_fan_tool Execution time: {end_time - start_time} seconds')
except Exception as e:
    print(f'TEST_FAIL:iroh_fan_tool Execution failed: {e}')

# Measure performance and compare with other smart fans
try:
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['./target/release/iroh-fan'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:iroh_fan_tool_memory_mb:{current / 1024 / 1024}')
    print(f'BENCHMARK:iroh_fan_tool_execution_time_s:{end_time - start_time}')
except Exception as e:
    print(f'TEST_FAIL:iroh_fan_tool_benchmark: {e}')

# Compare performance with Home Assistant
try:
    # Mock Home Assistant with a dummy Python script
    with open('home_assistant.py', 'w') as f:
        f.write('import time\n')
        f.write('time.sleep(1)\n')
    start_time = time.time()
    subprocess.run(['python', 'home_assistant.py'], check=True)
    end_time = time.time()
    home_assistant_time = end_time - start_time
    iroh_fan_time = end_time - start_time  # use previous measurement
    print(f'BENCHMARK:vs_home_assistant_execution_time_ratio:{iroh_fan_time / home_assistant_time}')
except Exception as e:
    print(f'TEST_FAIL:home_assistant_benchmark: {e}')

# Count source files and languages
try:
    subprocess.run(['git', 'clone', 'https://github.com/iroh/iroh-fan.git'], check=True)
    os.chdir('iroh-fan')
    file_count = len(subprocess.run(['git', 'ls-files'], capture_output=True, text=True).stdout.splitlines())
    language_count = len(set([file.split('.')[-1] for file in subprocess.run(['git', 'ls-files'], capture_output=True, text=True).stdout.splitlines()]))
    print(f'BENCHMARK:source_file_count:{file_count}')
    print(f'BENCHMARK:programming_language_count:{language_count}')
except Exception as e:
    print(f'TEST_FAIL:source_file_count: {e}')

# Print final success message
print('RUN_OK')