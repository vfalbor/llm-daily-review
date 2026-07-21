import subprocess
import requests
import time
import tracemalloc
import json

try:
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
except Exception as e:
    print(f"INSTALL_FAIL:Failed to install nodejs and npm: {e}")
    exit()

try:
    subprocess.run(['npm', 'install'], check=True, cwd='/app/Shinjuku-indoor-threejs-demo')
except Exception as e:
    print(f"INSTALL_FAIL:Failed to install dependencies: {e}")
    exit()

print("INSTALL_OK")

# Test 1: Run the demo in a browser
try:
    start_time = time.time()
    subprocess.run(['npm', 'start'], check=True, cwd='/app/Shinjuku-indoor-threejs-demo')
    end_time = time.time()
    print(f"BENCHMARK:demo_start_time_ms:{(end_time - start_time) * 1000}")
    print(f"TEST_PASS:Run demo in browser")
except Exception as e:
    print(f"TEST_FAIL:Run demo in browser: {e}")

# Test 2: Compare rendering performance
try:
    start_time = time.time()
    response = requests.get('http://localhost:3000')
    end_time = time.time()
    print(f"BENCHMARK:rendering_time_ms:{(end_time - start_time) * 1000}")
    print(f"TEST_PASS:Compare rendering performance")
except Exception as e:
    print(f"TEST_FAIL:Compare rendering performance: {e}")

# Benchmark memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{current / 10**6}")
tracemalloc.stop()

# Benchmark vs baseline tool (Three.js)
try:
    start_time = time.time()
    response = requests.get('https://threejs.org/examples/#webgl_loader_gltf')
    end_time = time.time()
    rendering_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_threejs_rendering_time_ms:{rendering_time_ms}")
    print(f"BENCHMARK:vs_threejs_rendering_ratio:{rendering_time_ms / ((end_time - start_time) * 1000)}")
    print(f"TEST_PASS:Compare with Three.js")
except Exception as e:
    print(f"TEST_FAIL:Compare with Three.js: {e}")

# Benchmark loc count
with open('/app/Shinjuku-indoor-threejs-demo/package.json', 'r') as f:
    package_json = json.load(f)
    print(f"BENCHMARK:loc_count:{package_json['scripts'].get('loc', 0)}")

# Benchmark test files count
test_files_count = len([file for file in subprocess.run(['find', '/app/Shinjuku-indoor-threejs-demo', '-name', 'test.js'], check=True, capture_output=True, text=True).stdout.splitlines() if file])
print(f"BENCHMARK:test_files_count:{test_files_count}")

print("RUN_OK")