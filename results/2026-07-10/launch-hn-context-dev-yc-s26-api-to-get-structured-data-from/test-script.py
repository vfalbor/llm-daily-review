import subprocess
import sys
import time
import requests
import tracemalloc

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)

# Install tool dependencies
try:
    subprocess.run(['npm', 'install', 'context-dev'], check=False)
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Measure installation time
start_time = time.time()
try:
    subprocess.run(['npm', 'install', 'context-dev'], check=True)
    install_time = time.time() - start_time
    print(f"BENCHMARK:install_time_s:{install_time:.2f}")
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Measure import time
start_time = time.time()
try:
    import requests
    import_time = time.time() - start_time
    print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_test:{str(e)}")

# Test API to extract data from a test website
def test_api():
    try:
        response = requests.get('https://www.context.dev/api/extract', params={'url': 'https://www.example.com', 'api_key': 'fake_api_key'})
        if response.status_code == 200:
            print("TEST_PASS:api_test")
        else:
            print(f"TEST_FAIL:api_test:{response.text}")
    except Exception as e:
        print(f"TEST_FAIL:api_test:{str(e)}")

# Measure response time
start_time = time.time()
try:
    response = requests.get('https://www.context.dev/api/extract', params={'url': 'https://www.example.com', 'api_key': 'fake_api_key'}, timeout=5)
    response_time = time.time() - start_time
    print(f"BENCHMARK:response_time_ms:{response_time*1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:response_time_test:{str(e)}")

# Compare performance vs Open Graph API
try:
    start_time = time.time()
    response = requests.get('https://opengraph.io/api/1.1/site/https://www.example.com')
    open_graph_response_time = time.time() - start_time
    ratio = response_time / open_graph_response_time
    print(f"BENCHMARK:vs_open_graph_response_time_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_FAIL:open_graph_comparison_test:{str(e)}")

# Measure memory usage
tracemalloc.start()
try:
    response = requests.get('https://www.context.dev/api/extract', params={'url': 'https://www.example.com', 'api_key': 'fake_api_key'})
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    tracemalloc.stop()
except Exception as e:
    print(f"TEST_FAIL:memory_usage_test:{str(e)}")

# Measure time to make 10 requests
start_time = time.time()
try:
    for _ in range(10):
        response = requests.get('https://www.context.dev/api/extract', params={'url': 'https://www.example.com', 'api_key': 'fake_api_key'})
    request_time = time.time() - start_time
    print(f"BENCHMARK:time_to_make_10_requests_ms:{request_time*1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:time_to_make_10_requests_test:{str(e)}")

test_api()

print("RUN_OK")