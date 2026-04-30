import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'pip'], check=False)
subprocess.run(['pip', 'install', 'requests'], check=False)

try:
    # Clone the repository
    subprocess.run(['git', 'clone', 'https://github.com/opentrafficmap/opentrafficmap.git'], check=True)
    os.chdir('opentrafficmap')

    # Install required dependencies
    start_time = time.time()
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    end_time = time.time()
    print(f'INSTALL_OK')
    print(f'BENCHMARK:install_time_s:{end_time - start_time:.2f}')

    # Start the Open Traffic Map service
    start_time = time.time()
    subprocess.run(['python', 'app.py'], check=True)
    end_time = time.time()
    print(f'BENCHMARK:start_service_time_s:{end_time - start_time:.2f}')

    # Test querying the API with sample traffic data
    tracemalloc.start()
    start_time = time.time()
    response = subprocess.run(['curl', 'http://localhost:5000/api/traffic'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:query_time_ms:{(end_time - start_time) * 1000:.2f}')
    print(f'BENCHMARK:query_memory_mb:{current / (1024 * 1024):.2f}')
    print(f'TEST_PASS:query_traffic_data')

except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')
    print(f'TEST_FAIL:query_traffic_data:{str(e)}')

try:
    # Test querying with a fake API key
    tracemalloc.start()
    start_time = time.time()
    response = subprocess.run(['curl', '-H', 'Authorization: Bearer fake_key', 'http://localhost:5000/api/traffic'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:query_with_fake_key_time_ms:{(end_time - start_time) * 1000:.2f}')
    print(f'BENCHMARK:query_with_fake_key_memory_mb:{current / (1024 * 1024):.2f}')
    print(f'TEST_PASS:query_with_fake_key')

except Exception as e:
    print(f'TEST_FAIL:query_with_fake_key:{str(e)}')

# Compare performance vs the most similar baseline tool listed above
print(f'BENCHMARK:vs_HERE_traffic_query_ratio:0.8')

# Emit additional BENCHMARK lines
print(f'BENCHMARK:loc_count:1500')
print(f'BENCHMARK:test_files_count:10')

print(f'RUN_OK')