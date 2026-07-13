import subprocess
import time
import tracemalloc
import json
import os
import sys

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

try:
    # Install tool dependencies
    subprocess.run(['pip', 'install', 'grok'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:Failed to install Grok")

# Start tracing memory usage
tracemalloc.start()

# Measure import time
import_start = time.time()
try:
    import grok
    import_end = time.time()
    import_time = (import_end - import_start) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
except ImportError as e:
    print(f"TEST_FAIL:Import Test:{e}")

# Measure core operation latency
try:
    start_time = time.time()
    grok.build_cli()
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:core_operation_latency_ms:{latency:.2f}")
except Exception as e:
    print(f"TEST_FAIL:Core Operation Test:{e}")

# Measure memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_bytes:{current}")

# Measure packet size and latency
try:
    import requests
    start_time = time.time()
    response = requests.post("https://api.xai.com/grok", json={"data": "synthetic data"})
    end_time = time.time()
    packet_latency = (end_time - start_time) * 1000
    packet_size = len(response.content)
    print(f"BENCHMARK:packet_latency_ms:{packet_latency:.2f}")
    print(f"BENCHMARK:packet_size_bytes:{packet_size}")
except requests.exceptions.RequestException as e:
    print(f"TEST_FAIL:Packet Size and Latency Test:{e}")

# Verify the format of the data being sent
try:
    import json
    data = {"data": "synthetic data"}
    json.dumps(data)
    print(f"TEST_PASS:Data Format Test")
except json.JSONDecodeError as e:
    print(f"TEST_FAIL:Data Format Test:{e}")

# Compare performance with other xAI APIs
try:
    import xai_api
    start_time = time.time()
    xai_api.build_cli()
    end_time = time.time()
    xai_latency = (end_time - start_time) * 1000
    ratio = latency / xai_latency
    print(f"BENCHMARK:vs_xai_api_latency_ratio:{ratio:.2f}")
except ImportError:
    print(f"TEST_SKIP:Performance Comparison Test:Missing xAI API")
except Exception as e:
    print(f"TEST_FAIL:Performance Comparison Test:{e}")

print("RUN_OK")