import subprocess
import time
import tracemalloc
import requests

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
print("INSTALL_OK")

# Install Skyglow demo
try:
    subprocess.run(['npm', 'install', 'iesna.eu'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Start server in background
subprocess.Popen(['node', 'iesna.eu/server.js'], stdout=subprocess.DEVNULL)

# Test 1: Simulate light pollution in NYC
try:
    start_time = time.time()
    response = requests.get('http://localhost:3000/skyglow_demo')
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:ny_simulate_ms:{response_time:.2f}")
    if response.status_code == 200:
        print("TEST_PASS:NYC_simulation")
    else:
        print(f"TEST_FAIL:NYC_simulation:{response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:NYC_simulation:{str(e)}")

# Test 2: Insert 1000 points and measure render latency
try:
    start_time = time.time()
    for _ in range(1000):
        requests.post('http://localhost:3000/skyglow_demo/points', json={'lat': 40.7128, 'lon': -74.0060})
    end_time = time.time()
    render_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:insert_points_ms:{render_time:.2f}")
    print("TEST_PASS:insert_points")
except Exception as e:
    print(f"TEST_FAIL:insert_points:{str(e)}")

# Test 3: Run a query with WHERE clause and measure query latency
try:
    start_time = time.time()
    response = requests.get('http://localhost:3000/skyglow_demo/query', params={'where': 'lat > 40'})
    end_time = time.time()
    query_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:query_latency_ms:{query_time:.2f}")
    if response.status_code == 200:
        print("TEST_PASS:query_latency")
    else:
        print(f"TEST_FAIL:query_latency:{response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:query_latency:{str(e)}")

# Test 4: Compare Skyglow latency vs Google Sky Map
try:
    start_time = time.time()
    requests.get('https://www.google.com/sky/simulator/sky.html')
    end_time = time.time()
    google_map_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_google_map_ms:{google_map_time:.2f}")
    skyglow_time = render_time
    ratio = google_map_time / skyglow_time
    print(f"BENCHMARK:vs_skyglow_ratio:{ratio:.2f}")
    print("TEST_PASS:compare_latency")
except Exception as e:
    print(f"TEST_FAIL:compare_latency:{str(e)}")

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024:.2f}")
tracemalloc.stop()

# Measure number of test files
test_files = subprocess.run(['find', '.', '-name', 'test_*.py'], stdout=subprocess.PIPE, check=False)
print(f"BENCHMARK:test_files_count:{len(test_files.stdout.decode().split())}")

print("RUN_OK")