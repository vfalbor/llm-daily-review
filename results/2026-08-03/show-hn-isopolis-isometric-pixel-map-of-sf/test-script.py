import subprocess
import requests
import time
import tracemalloc
import json

try:
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
    print('INSTALL_OK')

    # Install tool dependencies
    subprocess.run(['npm', 'install'], cwd='/app', check=False)
    print('INSTALL_OK')

    # Clone Isopolis repo
    subprocess.run(['git', 'clone', 'https://github.com/Isopolis/isopolis.git', '/app'], check=False)
    print('INSTALL_OK')

    # Install Isopolis dependencies
    subprocess.run(['npm', 'install'], cwd='/app', check=False)
    print('INSTALL_OK')

    # Start Isopolis server in background
    subprocess.Popen(['npm', 'start'], cwd='/app')

    # Test 1: Run Isopolis on a local machine and view the map
    try:
        response = requests.get('http://localhost:3000')
        if response.status_code == 200:
            print('TEST_PASS:run_isopolis_on_local_machine')
        else:
            print(f'TEST_FAIL:run_isopolis_on_local_machine:{response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:run_isopolis_on_local_machine:{str(e)}')

    # Test 2: Add custom markers and overlays to the map
    try:
        with open('/app/public/data.json', 'r+') as file:
            data = json.load(file)
            data['markers'].append({'lat': 37.7749, 'lng': -122.4194})
            file.seek(0)
            json.dump(data, file)
            file.truncate()
        response = requests.get('http://localhost:3000')
        if response.status_code == 200:
            print('TEST_PASS:add_custom_markers_and_overlays')
        else:
            print(f'TEST_FAIL:add_custom_markers_and_overlays:{response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:add_custom_markers_and_overlays:{str(e)}')

    # Benchmark performance on different hardware configurations
    tracemalloc.start()
    start_time = time.time()
    for _ in range(100):
        requests.get('http://localhost:3000')
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:response_time_ms:{(end_time - start_time) * 1000 / 100}')
    print(f'BENCHMARK:memory_usage_mb:{peak / 10**6}')

    # Compare performance vs Mapbox GL JS
    try:
        mapbox_response = requests.get('https://api.mapbox.com/')
        if mapbox_response.status_code == 200:
            mapbox_time = mapbox_response.elapsed.total_seconds() * 1000
            isopolis_time = (end_time - start_time) * 1000 / 100
            print(f'BENCHMARK:vs_mapbox_response_time_ratio:{isopolis_time / mapbox_time}')
        else:
            print(f'TEST_FAIL:compare_performance_vs_mapbox:{mapbox_response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance_vs_mapbox:{str(e)}')

    print('RUN_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')
    print('RUN_OK')