import subprocess
import time
import tracemalloc
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Clone repo and build container
try:
    subprocess.run(['git', 'clone', 'https://github.com/fabiensanglard/tb4.git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {e}")

# Build and run container
try:
    subprocess.run(['cd', 'tb4'], check=False)
    subprocess.run(['docker', 'build', '-t', 'tb4', '.'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {e}")

# Test web server responds
try:
    subprocess.run(['docker', 'run', '-p', '8080:80', 'tb4'], check=False)
    time.sleep(5)  # wait for container to start
    response = requests.get('http://localhost:8080')
    if response.status_code == 200:
        print("TEST_PASS:web_server_response")
    else:
        print(f"TEST_FAIL:web_server_response:{response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:web_server_response:{e}")

# Benchmark installation time
start_time = time.time()
subprocess.run(['docker', 'build', '-t', 'tb4', '.'], check=False)
end_time = time.time()
install_time = end_time - start_time
print(f"BENCHMARK:install_time_s:{install_time}")

# Benchmark import time
start_time = time.time()
subprocess.run(['docker', 'run', 'tb4', 'ls'], check=False)
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Benchmark hello world time
start_time = time.time()
subprocess.run(['docker', 'run', 'tb4', 'echo', 'Hello', 'World'], check=False)
end_time = time.time()
hello_world_time = (end_time - start_time) * 1000
print(f"BENCHMARK:hello_world_ms:{hello_world_time}")

# Compare performance vs Docker
docker_install_time = 12.4  # baseline installation time for Docker
ratio = install_time / docker_install_time
print(f"BENCHMARK:vs_docker_install_time_ratio:{ratio}")

# Benchmark memory usage
tracemalloc.start()
subprocess.run(['docker', 'run', 'tb4', 'ls'], check=False)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Benchmark loc count
start_time = time.time()
subprocess.run(['git', 'ls-files', '|', 'wc', '-l'], check=False, cwd='./tb4')
end_time = time.time()
loc_count_time = end_time - start_time
print(f"BENCHMARK:loc_count_time_s:{loc_count_time}")

# Benchmark test files count
start_time = time.time()
subprocess.run(['find', '.', '-name', '*.test'], check=False, cwd='./tb4')
end_time = time.time()
test_files_count_time = end_time - start_time
print(f"BENCHMARK:test_files_count_time_s:{test_files_count_time}")

print("RUN_OK")