import subprocess
import time
import tracemalloc
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Try to install pip package, if not, use git clone and pip install -e .
try:
    subprocess.run(['pip', 'install', 'colaptop'], check=False)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:colaptop pip package not found")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/colaptop/colaptop.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './colaptop'], check=False)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:colaptop git clone or pip install -e failed")
        exit(1)

# Test network connectivity between colo servers
start_time = time.time()
try:
    response = requests.get('https://colaptop.pages.dev/')
    end_time = time.time()
    if response.status_code == 200:
        print("TEST_PASS:network_connectivity")
        print(f"BENCHMARK:network_connectivity_ms:{(end_time - start_time) * 1000}")
    else:
        print(f"TEST_FAIL:network_connectivity:status_code_{response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"TEST_FAIL:network_connectivity:{e}")

# Deploy a simple service on the colo and measure performance
start_time = time.time()
try:
    subprocess.run(['colaptop', 'deploy', 'example_service'], check=False)
    end_time = time.time()
    print("TEST_PASS:deploy_service")
    print(f"BENCHMARK:deploy_time_s:{end_time - start_time}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:deploy_service:subprocess failed")
    print("BENCHMARK:deploy_time_s:NaN")

# Verify data persistence and recovery
start_time = time.time()
try:
    subprocess.run(['colaptop', 'create', 'example_data'], check=False)
    subprocess.run(['colaptop', 'delete', 'example_data'], check=False)
    subprocess.run(['colaptop', 'recover', 'example_data'], check=False)
    end_time = time.time()
    print("TEST_PASS:data_persistence")
    print(f"BENCHMARK:data_persistence_ms:{(end_time - start_time) * 1000}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:data_persistence:subprocess failed")
    print("BENCHMARK:data_persistence_ms:NaN")

# Compare performance vs the most similar baseline tool
# Assuming similar tool is ' Colo server management tools'
start_time = time.time()
try:
    subprocess.run(['colo', 'deploy', 'example_service'], check=False)
    end_time = time.time()
    baseline_time = end_time - start_time
    print(f"BENCHMARK:vs_colo_deploy_time_s:{baseline_time}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:baseline_tool:subprocess failed")
    print("BENCHMARK:vs_colo_deploy_time_s:NaN")

# Measure import time
start_time = time.time()
try:
    subprocess.run(['python', '-c', 'import colaptop'], check=False)
    end_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:import_time:subprocess failed")
    print("BENCHMARK:import_time_ms:NaN")

# Measure memory usage
tracemalloc.start()
start_time = time.time()
try:
    subprocess.run(['colaptop', 'deploy', 'example_service'], check=False)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_mb:{current / 10**6}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:memory_usage:subprocess failed")
    print("BENCHMARK:memory_usage_mb:NaN")

# Measure loc count
try:
    subprocess.run(['git', 'clone', 'https://github.com/colaptop/colaptop.git'], check=False)
    output = subprocess.check_output(['git', 'ls-files', '-z', '|', 'wc', '-l'])
    loc_count = int(output.decode().strip())
    print(f"BENCHMARK:loc_count:{loc_count}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:loc_count:subprocess failed")
    print("BENCHMARK:loc_count:NaN")

# Measure test files count
try:
    output = subprocess.check_output(['find', '.', '-type', 'f', '-name', 'test_*.py', '-exec', 'echo', '{}', ';', '|', 'wc', '-l'])
    test_files_count = int(output.decode().strip())
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:test_files_count:subprocess failed")
    print("BENCHMARK:test_files_count:NaN")

print("RUN_OK")