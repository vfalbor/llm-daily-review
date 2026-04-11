import subprocess
import requests
import time
from urllib.parse import urlencode
import tracemalloc

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
        INSTALL_STATUS = 'OK'
    except subprocess.SubprocessError as e:
        INSTALL_STATUS = f'FAIL:{e}'
    print(f'INSTALL_{INSTALL_STATUS}')

def start_server():
    try:
        subprocess.run(['npm', 'install'], check=False)
        subprocess.run(['npm', 'start'], check=False)
        time.sleep(2)
    except subprocess.SubprocessError as e:
        print(f'TEST_FAIL:start_server:{e}')

def test_search_pardon():
    try:
        search_term = 'example'
        params = {'q': search_term}
        start_time = time.time()
        response = requests.get(f'https://pardonned.com/search', params=params)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:search_pardon_ms:{response_time}')
        if response.status_code == 200:
            print(f'TEST_PASS:search_pardon')
        else:
            print(f'TEST_FAIL:search_pardon:invalid_response_code_{response.status_code}')
    except requests.RequestException as e:
        print(f'TEST_FAIL:search_pardon:{e}')

def test_health_endpoint():
    try:
        start_time = time.time()
        response = requests.get('https://pardonned.com/health')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:health_check_ms:{response_time}')
        if response.status_code == 200:
            print(f'TEST_PASS:health_endpoint')
        else:
            print(f'TEST_FAIL:health_endpoint:invalid_response_code_{response.status_code}')
    except requests.RequestException as e:
        print(f'TEST_FAIL:health_endpoint:{e}')

def benchmark_performance():
    try:
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['npm', 'start'], check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_bytes:{current}')
        print(f'BENCHMARK:peak_memory_usage_bytes:{peak}')
        print(f'BENCHMARK:startup_time_s:{end_time - start_time}')
        tracemalloc.stop()
    except subprocess.SubprocessError as e:
        print(f'BENCHMARK:perf_error:{e}')

def compare_to_baseline():
    try:
        baseline_url = 'https://pardon.com'
        search_term = 'example'
        params = {'q': search_term}
        start_time = time.time()
        response = requests.get(f'{baseline_url}/search', params=params)
        end_time = time.time()
        baseline_response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_pardon_search_pardon_ms:{baseline_response_time}')
        ratio = baseline_response_time / 100
        print(f'BENCHMARK:vs_pardon_search_pardon_ratio:{ratio}')
    except requests.RequestException as e:
        print(f'BENCHMARK:vs_pardon_error:{e}')

install_dependencies()
start_server()
test_search_pardon()
test_health_endpoint()
benchmark_performance()
compare_to_baseline()
print('RUN_OK')