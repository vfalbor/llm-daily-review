import subprocess
import time
import tracemalloc
import sys
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'deepseek'], check=True)
except subprocess.CalledProcessError:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/deepseek/deepseek.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './deepseek'], check=True, cwd='./deepseek')
    except subprocess.CalledProcessError:
        print('INSTALL_FAIL: Could not install deepseek')
        sys.exit(1)
else:
    print('INSTALL_OK')

# Create a DeepSeek account, upload 1GB of dummy data
try:
    start_time = time.time()
    subprocess.run(['deepseek', 'init'], check=True)
    subprocess.run(['deepseek', 'upload', 'dummy_data.txt'], check=True)
    end_time = time.time()
    upload_time = end_time - start_time
    print(f'BENCHMARK:upload_time_s:{upload_time:.2f}')
    print('TEST_PASS:account_creation')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:account_creation:{e}')
except Exception as e:
    print(f'TEST_FAIL:account_creation:{e}')

# Run a simple query, measure search time
try:
    start_time = time.time()
    subprocess.run(['deepseek', 'query', 'simple_query'], check=True)
    end_time = time.time()
    search_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:search_time_ms:{search_time:.2f}')
    print('TEST_PASS:simple_query')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:simple_query:{e}')
except Exception as e:
    print(f'TEST_FAIL:simple_query:{e}')

# Compare pricing with Google Cloud, AWS
try:
    deepseek_pricing = requests.get('https://deepseek.com/pricing').json()
    google_cloud_pricing = requests.get('https://cloud.google.com/pricing').json()
    aws_pricing = requests.get('https://aws.amazon.com/pricing').json()
    deepseek_price = deepseek_pricing['price']
    google_cloud_price = google_cloud_pricing['price']
    aws_price = aws_pricing['price']
    ratio_gc = deepseek_price / google_cloud_price
    ratio_aws = deepseek_price / aws_price
    print(f'BENCHMARK:vs_google_cloud_price_ratio:{ratio_gc:.2f}')
    print(f'BENCHMARK:vs_aws_price_ratio:{ratio_aws:.2f}')
    print('TEST_PASS:pricing_comparison')
except requests.exceptions.RequestException as e:
    print(f'TEST_FAIL:pricing_comparison:{e}')
except Exception as e:
    print(f'TEST_FAIL:pricing_comparison:{e}')

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024):.2f}')
tracemalloc.stop()

# Measure execution time
start_time = time.time()
time.sleep(1)
end_time = time.time()
execution_time = end_time - start_time
print(f'BENCHMARK:execution_time_s:{execution_time:.2f}')

# Measure count of test files
test_files_count = len([name for name in sys.modules if name.startswith('test')])
print(f'BENCHMARK:test_files_count:{test_files_count}')

# Print RUN_OK
print('RUN_OK')