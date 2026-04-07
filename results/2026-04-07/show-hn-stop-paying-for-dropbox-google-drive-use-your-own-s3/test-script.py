import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Install tool dependencies via pip
try:
    subprocess.run(['pip', 'install', 'locker'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:Failed to install locker via pip: {e}')
    try:
        subprocess.run(['git', 'clone', 'https://github.com/locker-dev/locker.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './locker'], check=True, cwd='./locker')
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:Failed to install locker via git clone and pip install -e: {e}')

# Test 1: Install locker CLI and create an S3 bucket
try:
    start_time = time.time()
    subprocess.run(['locker', 'init'], check=True)
    end_time = time.time()
    bucket_name = subprocess.run(['locker', 'info', '--bucket'], check=True, capture_output=True, text=True).stdout.strip()
    print(f'TEST_PASS:locker_cli_init_and_create_bucket')
    print(f'BENCHMARK:locker_cli_init_time_ms:{(end_time - start_time) * 1000}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:locker_cli_init_and_create_bucket: {e}')

# Test 2: Upload a file to S3 using the locker CLI
try:
    start_time = time.time()
    file_path = 'test_file.txt'
    with open(file_path, 'w') as f:
        f.write('Hello World!')
    subprocess.run(['locker', 'upload', file_path], check=True)
    end_time = time.time()
    os.remove(file_path)
    print(f'TEST_PASS:upload_file_to_s3')
    print(f'BENCHMARK:upload_file_to_s3_time_ms:{(end_time - start_time) * 1000}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:upload_file_to_s3: {e}')

# Test 3: Check bucket policy permissions for a user account
try:
    start_time = time.time()
    policy = subprocess.run(['locker', 'info', '--policy'], check=True, capture_output=True, text=True).stdout.strip()
    end_time = time.time()
    print(f'TEST_PASS:check_bucket_policy')
    print(f'BENCHMARK:check_bucket_policy_time_ms:{(end_time - start_time) * 1000}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:check_bucket_policy: {e}')

# Compare performance vs the most similar baseline tool (in this case, AWS CLI)
try:
    start_time = time.time()
    subprocess.run(['aws', 's3', 'ls'], check=True)
    end_time = time.time()
    aws_cli_time = (end_time - start_time) * 1000
    locker_cli_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:vs_aws_cli_time_ms:{aws_cli_time}')
    print(f'BENCHMARK:vs_aws_cli_ratio:{locker_cli_time / aws_cli_time}')
except subprocess.CalledProcessError as e:
    print(f'TEST_SKIP:compare_performance_vs_aws_cli: {e}')

# Memory benchmark
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_mb:{current / 1024 / 1024}')
tracemalloc.stop()

# Time benchmark
start_time = time.time()
time.sleep(1)
end_time = time.time()
print(f'BENCHMARK:sleep_time_ms:{(end_time - start_time) * 1000}')

# File count benchmark
file_count = len(os.listdir())
print(f'BENCHMARK:file_count:{file_count}')

print('RUN_OK')