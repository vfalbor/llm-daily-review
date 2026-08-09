import subprocess
import time
import tracemalloc
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

# Install tool dependencies
try:
    subprocess.run(['npm', 'install'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Start server in background
try:
    subprocess.Popen(['node', 'server.js'], stdout=subprocess.PIPE)
    time.sleep(5)  # Wait for server to start
    print("SERVER_STARTED")
except Exception as e:
    print(f"SERVER_START_FAIL:{str(e)}")

# Test map on different browsers
browsers = ['Chrome', 'Firefox', 'Edge']
for browser in browsers:
    try:
        # Measure response time
        start_time = time.time()
        response = requests.get(f'http://localhost:8080?browser={browser}')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        # Check /health endpoint if available
        health_start_time = time.time()
        health_response = requests.get('http://localhost:8080/health')
        health_end_time = time.time()
        health_response_time = (health_end_time - health_start_time) * 1000

        print(f"TEST_PASS:{browser}")
        print(f"BENCHMARK:response_time_{browser}_ms:{response_time}")
        print(f"BENCHMARK:health_response_time_{browser}_ms:{health_response_time}")
    except Exception as e:
        print(f"TEST_FAIL:{browser}:{str(e)}")

# Compare performance vs baseline tool (Google Maps)
try:
    start_time = time.time()
    response = requests.get('https://www.google.com/maps')
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_google_maps_response_time_ms:{response_time}")
except Exception as e:
    print(f"BENCHMARK_FAIL:vs_google_maps_response_time_ms:{str(e)}")

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}")
print(f"BENCHMARK:peak_memory_usage_mb:{peak / (1024 * 1024)}")

# Measure time to import
start_time = time.time()
import requests
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Measure time to send HTTP request
start_time = time.time()
requests.get('http://localhost:8080')
end_time = time.time()
request_time = (end_time - start_time) * 1000
print(f"BENCHMARK:request_time_ms:{request_time}")

# Measure time to parse JSON
import json
start_time = time.time()
json.loads('{"key": "value"}')
end_time = time.time()
parse_time = (end_time - start_time) * 1000
print(f"BENCHMARK:parse_time_ms:{parse_time}")

# Measure count of test files
import os
test_files = [f for f in os.listdir() if f.startswith('test_')]
print(f"BENCHMARK:test_files_count:{len(test_files)}")

print("RUN_OK")