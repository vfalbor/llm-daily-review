import subprocess
import time
import tracemalloc
import requests

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        subprocess.run(['npm', 'install'], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_launch_tutorial():
    try:
        start_time = time.time()
        subprocess.run(['npm', 'start'], check=True)
        response = requests.get('http://localhost:3000')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:launch_time_ms:{response_time}')
        if response.status_code == 200:
            print('TEST_PASS:launch_tutorial')
        else:
            print(f'TEST_FAIL:launch_tutorial:Failed to launch tutorial')
    except Exception as e:
        print(f'TEST_FAIL:launch_tutorial:{str(e)}')

def test_interact_with_code():
    try:
        start_time = time.time()
        response = requests.post('http://localhost:3000/compile', data={'code': 'println("Hello World")'})
        end_time = time.time()
        compile_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:compile_time_ms:{compile_time}')
        if response.status_code == 200:
            print('TEST_PASS:interact_with_code')
        else:
            print(f'TEST_FAIL:interact_with_code:Failed to compile code')
    except Exception as e:
        print(f'TEST_FAIL:interact_with_code:{str(e)}')

def test_compare_vs_baseline():
    try:
        start_time = time.time()
        response = requests.get('https://www.freecodecamp.org')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_freecodecamp_response_time_ms:{response_time}')
        if response.status_code == 200:
            print('TEST_PASS:compare_vs_baseline')
        else:
            print(f'TEST_FAIL:compare_vs_baseline:Failed to compare with baseline')
    except Exception as e:
        print(f'TEST_FAIL:compare_vs_baseline:{str(e)}')

def test_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['npm', 'start'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_bytes:{peak}')
    except Exception as e:
        print(f'TEST_FAIL:test_memory_usage:{str(e)}')

def main():
    install_dependencies()
    test_launch_tutorial()
    test_interact_with_code()
    test_compare_vs_baseline()
    test_memory_usage()
    print('RUN_OK')

if __name__ == "__main__":
    main()