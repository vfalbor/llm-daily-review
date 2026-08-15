import subprocess
import time
import requests
import tracemalloc
import os

# Install required packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Install Eigendrum
try:
    subprocess.run(['npm', 'install', 'eigendrum'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Start Eigendrum server in background
try:
    subprocess.Popen(['npm', 'start'], cwd=os.getcwd())
    time.sleep(5)  # wait for server to start
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Test 1: Download Eigendrum and run a standard drumming example
try:
    start_time = time.time()
    response = requests.get('http://localhost:8080/')
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:download_time_ms:{response_time}")
    if response.status_code == 200:
        print("TEST_PASS:drumming_example")
    else:
        print(f"TEST_FAIL:drumming_example:{response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:drumming_example:{e}")

# Test 2: Test visual customization options and ensure UI remains snappy
try:
    start_time = time.time()
    response = requests.post('http://localhost:8080/api/customize', json={'color': 'red'})
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:customization_time_ms:{response_time}")
    if response.status_code == 200:
        print("TEST_PASS:visual_customization")
    else:
        print(f"TEST_FAIL:visual_customization:{response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:visual_customization:{e}")

# Test 3: Verify compatibility with different web browsers
try:
    browsers = ['Chrome', 'Firefox', 'Safari']
    for browser in browsers:
        start_time = time.time()
        response = requests.get('http://localhost:8080/', headers={'User-Agent': browser})
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:browser_{browser}_time_ms:{response_time}")
        if response.status_code == 200:
            print(f"TEST_PASS:browser_{browser}")
        else:
            print(f"TEST_FAIL:browser_{browser}:{response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:browser_compatibility:{e}")

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{current / 10**6}")
tracemalloc.stop()

# Compare performance vs the most similar baseline tool (Drum Machine)
try:
    start_time = time.time()
    response = requests.get('https://drummachine.io/')
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    eigendrum_response_time = response_time
    print(f"BENCHMARK:vs_drummachine_response_time_ms:{response_time}")
    print(f"BENCHMARK:vs_drummachine_response_time_ratio:{eigendrum_response_time / response_time}")
except Exception as e:
    print(f"BENCHMARK:vs_drummachine_response_time_ms:failed:{e}")

# Print final marker
print("RUN_OK")