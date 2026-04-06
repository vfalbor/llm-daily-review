import subprocess
import time
import tracemalloc
import numpy as np

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)

# Install docking via pip
start_time = time.time()
try:
    subprocess.run(['pip', 'install', 'docking'], check=True)
    end_time = time.time()
    print('INSTALL_OK')
    print(f'BENCHMARK:install_time_s:{end_time - start_time:.2f}')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:Failed to install docking via pip: {e}')
    # Fallback to installing from source
    try:
        subprocess.run(['git', 'clone', 'https://github.com/yourname/docking.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './docking'], check=True)
        end_time = time.time()
        print(f'BENCHMARK:install_time_s:{end_time - start_time:.2f}')
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:Failed to install docking from source: {e}')

# Install required tools for comparison
try:
    subprocess.run(['pip', 'install', 'dmenu'], check=True)
    subprocess.run(['pip', 'install', 'Rofi'], check=True)
    subprocess.run(['pip', 'install', 'i3-dock'], check=True)
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:Failed to install baseline tools: {e}')

# Measure application launch time
try:
    start_time = time.time()
    subprocess.run(['docking'], check=True)
    end_time = time.time()
    launch_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:launch_time_ms:{launch_time:.2f}')
    print('TEST_PASS:application_launch')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:application_launch:Failed to launch docking: {e}')

# Measure launch time for baseline tools
try:
    start_time = time.time()
    subprocess.run(['dmenu'], check=True)
    end_time = time.time()
    launch_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:baseline_dmenu_launch_time_ms:{launch_time:.2f}')
    ratio = (launch_time / ((end_time - start_time) * 1000)) if 'launch_time_ms' in locals() else np.nan
    print(f'BENCHMARK:vs_dmenu_launch_time_ratio:{ratio:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:baseline_dmenu_launch:Failed to launch dmenu: {e}')

try:
    start_time = time.time()
    subprocess.run(['Rofi'], check=True)
    end_time = time.time()
    launch_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:baseline_rofi_launch_time_ms:{launch_time:.2f}')
    ratio = (launch_time / ((end_time - start_time) * 1000)) if 'launch_time_ms' in locals() else np.nan
    print(f'BENCHMARK:vs_rofi_launch_time_ratio:{ratio:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:baseline_rofi_launch:Failed to launch Rofi: {e}')

try:
    start_time = time.time()
    subprocess.run(['i3-dock'], check=True)
    end_time = time.time()
    launch_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:baseline_i3_dock_launch_time_ms:{launch_time:.2f}')
    ratio = (launch_time / ((end_time - start_time) * 1000)) if 'launch_time_ms' in locals() else np.nan
    print(f'BENCHMARK:vs_i3_dock_launch_time_ratio:{ratio:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:baseline_i3_dock_launch:Failed to launch i3-dock: {e}')

# Measure memory usage
tracemalloc.start()
try:
    subprocess.run(['docking'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{current:.2f}')
    tracemalloc.stop()
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:memory_usage:Failed to measure memory usage: {e}')

# Measure execution time for custom docking configuration
try:
    start_time = time.time()
    subprocess.run(['docking', '--config', './custom_config'], check=True)
    end_time = time.time()
    execution_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:custom_config_execution_time_ms:{execution_time:.2f}')
    print('TEST_PASS:custom_docking_configuration')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:custom_docking_configuration:Failed to create custom docking configuration: {e}')

# Print final marker
print('RUN_OK')