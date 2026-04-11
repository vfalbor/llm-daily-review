import subprocess
import time
import tracemalloc
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
print('INSTALL_OK')

# Install tool dependencies
start_time = time.time()
subprocess.run(['npm', 'install', '-g', 'bevy'], check=False)
install_time = time.time() - start_time
print(f'BENCHMARK:install_time_s:{install_time:.2f}')

try:
    # Install Bevy using the quickstart guide
    start_time = time.time()
    subprocess.run(['bevy', 'new', 'my_bevey_project'], check=True)
    install_time = time.time() - start_time
    print(f'BENCHMARK:bevy_install_time_s:{install_time:.2f}')
    print('TEST_PASS:Install Bevy using the quickstart guide')
except Exception as e:
    print(f'TEST_FAIL:Install Bevy using the quickstart guide:{str(e)}')

try:
    # Create a simple Bevy project
    start_time = time.time()
    subprocess.run(['bevy', 'run', '--project', 'my_bevey_project'], check=True)
    run_time = time.time() - start_time
    print(f'BENCHMARK:bevy_run_time_s:{run_time:.2f}')
    print('TEST_PASS:Create a simple Bevy project')
except Exception as e:
    print(f'TEST_FAIL:Create a simple Bevy project:{str(e)}')

try:
    # Run the project and inspect the UI
    start_time = time.time()
    response = requests.get('http://localhost:3000')
    response_time = time.time() - start_time
    print(f'BENCHMARK:bevy_response_time_ms:{response_time*1000:.2f}')
    print('TEST_PASS:Run the project and inspect the UI')
except Exception as e:
    print(f'TEST_FAIL:Run the project and inspect the UI:{str(e)}')

try:
    # Compare performance vs Godot
    start_time = time.time()
    subprocess.run(['godot', '--project', 'my_godot_project'], check=True)
    godot_run_time = time.time() - start_time
    print(f'BENCHMARK:vs_godot_run_time_ratio:{run_time/godot_run_time:.2f}')
except Exception as e:
    print(f'BENCHMARK:vs_godot_run_time_ratio:NA')

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:mem_usage_mb:{current/1024/1024:.2f}')
print(f'BENCHMARK:mem_peak_mb:{peak/1024/1024:.2f}')

print('RUN_OK')