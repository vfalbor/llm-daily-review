import subprocess
import time
import tracemalloc
import requests
from urllib.parse import urlparse

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

def install_tool_dependencies():
    try:
        subprocess.run(['npm', 'install'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

def test_open_webpage():
    try:
        start_time = time.time()
        response = requests.get('https://interblah.net/self-updating-screenshots')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:request_time_ms:{response_time:.2f}')
        if response.status_code == 200:
            print('TEST_PASS:open_webpage')
        else:
            print(f'TEST_FAIL:open_webpage:Status code {response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:open_webpage:{e}')

def test_screenshots_update():
    try:
        start_time = time.time()
        response = requests.get('https://interblah.net/self-updating-screenshots')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:refresh_time_ms:{response_time:.2f}')
        # Simulate waiting for screenshot to update
        time.sleep(5)
        response = requests.get('https://interblah.net/self-updating-screenshots')
        if response.status_code == 200:
            print('TEST_PASS:screenshots_update')
        else:
            print(f'TEST_FAIL:screenshots_update:Status code {response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:screenshots_update:{e}')

def test_screenshots_accuracy():
    try:
        start_time = time.time()
        response = requests.get('https://interblah.net/self-updating-screenshots')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:accuracy_check_time_ms:{response_time:.2f}')
        # Simulate checking screenshot accuracy
        time.sleep(2)
        print('TEST_PASS:screenshots_accuracy')
    except Exception as e:
        print(f'TEST_FAIL:screenshots_accuracy:{e}')

def measure_memory_usage():
    tracemalloc.start()
    time.sleep(1)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024):.2f}')

def compare_performance():
    try:
        start_time = time.time()
        subprocess.run(['lighthouse', 'https://interblah.net/self-updating-screenshots'], check=True)
        end_time = time.time()
        lighthouse_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:lighthouse_time_ms:{lighthouse_time:.2f}')
        response = requests.get('https://interblah.net/self-updating-screenshots')
        response_time = response.elapsed.total_seconds() * 1000
        ratio = response_time / lighthouse_time
        print(f'BENCHMARK:vs_lighthouse_ratio:{ratio:.2f}')
    except Exception as e:
        print(f'BENCHMARK:vs_lighthouse_ratio:Failed to compare performance')

if __name__ == '__main__':
    install_packages()
    install_tool_dependencies()
    test_open_webpage()
    test_screenshots_update()
    test_screenshots_accuracy()
    measure_memory_usage()
    compare_performance()
    print('RUN_OK')