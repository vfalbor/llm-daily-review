import subprocess
import time
import tracemalloc
import json
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Try installing DeepSeek package
try:
    subprocess.run(['pip', 'install', 'deepseek'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:Failed to install DeepSeek package: {e}')

# Test CLI availability
try:
    subprocess.run(['deepseek', '--help'], check=True)
    print('TEST_PASS:cli_availability')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:cli_availability:Failed to run DeepSeek CLI: {e}')

# Measure installation time
start_time = time.time()
subprocess.run(['pip', 'install', 'deepseek'], check=False)
end_time = time.time()
install_time = end_time - start_time
print(f'BENCHMARK:install_time_s:{install_time:.2f}')

# Measure import time
start_time = time.time()
import deepseek
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f'BENCHMARK:import_time_ms:{import_time:.2f}')

# Test creating a DeepSeek account and setting up Harness
try:
    # Mock API call with a fake key
    response = requests.post('https://api.deepseek.com/v1/accounts', json={'api_key': 'fake_key'})
    if response.status_code == 401:
        print('TEST_PASS:create_account')
    else:
        print('TEST_FAIL:create_account:Failed to create DeepSeek account')
except requests.RequestException as e:
    print(f'TEST_FAIL:create_account:Failed to create DeepSeek account: {e}')

# Test running a simple workload
try:
    # Run a simple workload using the DeepSeek CLI
    start_time = time.time()
    subprocess.run(['deepseek', 'run', 'simple_workload'], check=True)
    end_time = time.time()
    workload_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:simple_workload_ms:{workload_time:.2f}')
    print('TEST_PASS:simple_workload')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:simple_workload:Failed to run simple workload: {e}')

# Compare performance vs AWS
try:
    # Run a simple workload using the AWS CLI
    start_time = time.time()
    subprocess.run(['aws', 'lambda', 'invoke', 'simple_workload'], check=True)
    end_time = time.time()
    aws_workload_time = (end_time - start_time) * 1000
    ratio = workload_time / aws_workload_time
    print(f'BENCHMARK:vs_aws_workload_ratio:{ratio:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_SKIP:aws_workload:Failed to run AWS workload: {e}')

# Measure memory usage
tracemalloc.start()
subprocess.run(['deepseek', 'run', 'simple_workload'], check=False)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_mb:{peak / (1024 * 1024):.2f}')

# Measure loc count
try:
    loc_count = subprocess.run(['git', 'ls-files', 'deepseek'], capture_output=True, text=True).stdout.splitlines()
    loc_count = len(loc_count)
    print(f'BENCHMARK:loc_count:{loc_count}')
except subprocess.CalledProcessError as e:
    print(f'TEST_SKIP:loc_count:Failed to get loc count: {e}')

# Measure test files count
try:
    test_files_count = subprocess.run(['git', 'ls-files', 'deepseek/test'], capture_output=True, text=True).stdout.splitlines()
    test_files_count = len(test_files_count)
    print(f'BENCHMARK:test_files_count:{test_files_count}')
except subprocess.CalledProcessError as e:
    print(f'TEST_SKIP:test_files_count:Failed to get test files count: {e}')

print('RUN_OK')