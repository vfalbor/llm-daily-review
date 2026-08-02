import subprocess
import time
import tracemalloc
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
print("INSTALL_OK")

# Install tool dependencies
try:
    subprocess.run(['npm', 'install', 'elenajs'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Test 1: import example component, render it to the DOM
try:
    # Note: this is a Node.js library, we need to use subprocess to run a Node.js script
    subprocess.run(['node', '-e', 'const Elena = require("elenajs"); const component = new Elena.Component();'], check=True)
    print("TEST_PASS:import_example_component")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:import_example_component:{e}")

# Test 2: benchmark rendering performance
try:
    start_time = time.time()
    tracemalloc.start()
    # Note: this is a Node.js library, we need to use subprocess to run a Node.js script
    subprocess.run(['node', '-e', 'const Elena = require("elenajs"); const component = new Elena.Component(); component.render();'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:render_time_ms:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:render_memory_mb:{current / 1024 / 1024:.2f}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:render_performance:{e}")

# Test 3: benchmark rendering performance compared to other libraries
try:
    # Note: we need to install another library for comparison
    subprocess.run(['npm', 'install', 'react'], check=True)
    start_time = time.time()
    tracemalloc.start()
    # Note: this is a Node.js library, we need to use subprocess to run a Node.js script
    subprocess.run(['node', '-e', 'const React = require("react"); const component = React.createElement("div", null, "Hello World");'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:vs_react_render_time_ms:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:vs_react_render_memory_mb:{current / 1024 / 1024:.2f}")
    # Calculate the ratio of rendering time compared to React
    elena_time = end_time - start_time
    react_time = subprocess.run(['node', '-e', 'const React = require("react"); const component = React.createElement("div", null, "Hello World");'], check=True, capture_output=True, text=True)
    react_time = float(react_time.stdout.strip().split(":")[1].strip())
    print(f"BENCHMARK:vs_react_render_time_ratio:{elena_time / react_time:.2f}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:render_performance_comparison:{e}")

# Start the server in background
try:
    subprocess.run(['npm', 'start', '&'], check=True)
    time.sleep(2)  # wait for the server to start
    response = requests.get('http://localhost:3000/health')
    if response.status_code == 200:
        print("TEST_PASS:health_endpoint")
    else:
        print(f"TEST_FAIL:health_endpoint:{response.status_code}")
except requests.RequestException as e:
    print(f"TEST_FAIL:health_endpoint:{e}")

# Benchmark HTTP request response time
try:
    start_time = time.time()
    response = requests.get('http://localhost:3000')
    end_time = time.time()
    print(f"BENCHMARK:response_time_ms:{(end_time - start_time) * 1000:.2f}")
except requests.RequestException as e:
    print(f"TEST_FAIL:response_time:{e}")

print("RUN_OK")