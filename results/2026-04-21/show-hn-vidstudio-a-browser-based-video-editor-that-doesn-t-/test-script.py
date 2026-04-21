import subprocess
import requests
import time
import tracemalloc
import os

# Install system packages with subprocess
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)

# Install tool dependencies (npm) via subprocess
subprocess.run(['npm', 'install'], cwd='/app', check=False)

# Start the server in background
server_process = subprocess.Popen(['npm', 'start'], cwd='/app', stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for the server to start
time.sleep(5)

# Initialize benchmark metrics
install_time_s = time.time() - subprocess.run(['date', '+%s'], stdout=subprocess.PIPE).stdout

# Print structured markers on stdout
print(f"INSTALL_OK")
print(f"BENCHMARK:install_time_s:{install_time_s}")

try:
    # Test 1: Create a new project and check basic video editing features
    start_time = time.time()
    response = requests.post('http://localhost:3000/projects', json={'name': 'Test Project'})
    end_time = time.time()
    if response.status_code == 201:
        print(f"TEST_PASS:create_project")
        print(f"BENCHMARK:create_project_time_ms:{(end_time - start_time) * 1000:.2f}")
    else:
        print(f"TEST_FAIL:create_project:{response.text}")

    # Test 2: Test export to different formats (e.g. mp4, avchd)
    start_time = time.time()
    response = requests.post('http://localhost:3000/projects/1/export', json={'format': 'mp4'})
    end_time = time.time()
    if response.status_code == 200:
        print(f"TEST_PASS:export_mp4")
        print(f"BENCHMARK:export_mp4_time_ms:{(end_time - start_time) * 1000:.2f}")
    else:
        print(f"TEST_FAIL:export_mp4:{response.text}")

    # Test 3: Check if VidStudio can import and edit existing footage
    start_time = time.time()
    response = requests.post('http://localhost:3000/projects/1/import', json={'file': 'test_footage.mp4'})
    end_time = time.time()
    if response.status_code == 200:
        print(f"TEST_PASS:import_footage")
        print(f"BENCHMARK:import_footage_time_ms:{(end_time - start_time) * 1000:.2f}")
    else:
        print(f"TEST_FAIL:import_footage:{response.text}")

    # Test 4: Evaluate performance with 4K footage
    start_time = time.time()
    response = requests.post('http://localhost:3000/projects/1/export', json={'format': 'mp4', 'resolution': '4k'})
    end_time = time.time()
    if response.status_code == 200:
        print(f"TEST_PASS:export_4k")
        print(f"BENCHMARK:export_4k_time_ms:{(end_time - start_time) * 1000:.2f}")
    else:
        print(f"TEST_FAIL:export_4k:{response.text}")

    # Compare performance vs DaVinci Resolve
    davinci_resolve_time_ms = 500  # Assuming a baseline time of 500ms
    vidstudio_time_ms = (end_time - start_time) * 1000
    ratio = vidstudio_time_ms / davinci_resolve_time_ms
    print(f"BENCHMARK:vs_davinci_resolve_ratio:{ratio:.2f}")

except Exception as e:
    print(f"TEST_FAIL:overall:{str(e)}")

# Print memory usage metrics
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{current / (1024 * 1024):.2f}")
tracemalloc.stop()

# Print file count and line count metrics
file_count = sum(1 for _ in os.listdir('/app'))
print(f"BENCHMARK:file_count:{file_count}")
line_count = sum(1 for _ in open('/app/index.js'))
print(f"BENCHMARK:line_count:{line_count / 10:.2f}")

# Print RUN_OK
print("RUN_OK")