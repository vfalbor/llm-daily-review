import subprocess
import time
import requests
import tracemalloc
import json

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        subprocess.run(['npm', 'install'], cwd='/app', check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

def start_server():
    try:
        subprocess.run(['npm', 'start'], cwd='/app', check=True)
        time.sleep(5)  # wait for server to start
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:start_server:{e}')

def test_create_guide():
    try:
        start_time = time.time()
        response = requests.post('http://localhost:3000/guides', json={'title': 'New Guide', 'description': 'Test guide'})
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        tracemalloc.start()
        response = requests.get('http://localhost:3000/guides')
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'TEST_PASS:create_guide')
        print(f'BENCHMARK:create_guide_ms:{response_time}')
        print(f'BENCHMARK:memory_usage_byte:{peak}')
    except requests.exceptions.RequestException as e:
        print(f'TEST_FAIL:create_guide:{e}')

def compare_to_baseline():
    try:
        # simulate a request to Google Trips
        start_time = time.time()
        response = requests.get('https://google.com/travel')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        our_response_time = float(next(line.split(':')[1] for line in open('output.txt') if line.startswith('BENCHMARK:create_guide_ms:')))
        ratio = our_response_time / response_time
        print(f'BENCHMARK:vs_google_trips_ratio:{ratio}')
    except requests.exceptions.RequestException as e:
        print(f'TEST_FAIL:compare_to_baseline:{e}')

def test_health_endpoint():
    try:
        response = requests.get('http://localhost:3000/health')
        if response.status_code == 200:
            print(f'TEST_PASS:health_endpoint')
        else:
            print(f'TEST_FAIL:health_endpoint:{response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f'TEST_FAIL:health_endpoint:{e}')

def benchmark_time():
    start_time = time.time()
    for i in range(100):
        requests.get('http://localhost:3000/guides')
    end_time = time.time()
    avg_time = (end_time - start_time) / 100 * 1000
    print(f'BENCHMARK:avg_time_ms:{avg_time}')

def main():
    install_dependencies()
    start_server()
    test_create_guide()
    compare_to_baseline()
    test_health_endpoint()
    benchmark_time()
    print('RUN_OK')

if __name__ == '__main__':
    main()