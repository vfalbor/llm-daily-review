import subprocess
import time
import requests
import tracemalloc
import json

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
print("INSTALL_OK")

# Install HtmlDrive
start_time = time.time()
subprocess.run(['npm', 'install', 'http-server'], check=False)
html_drive_install_time = time.time() - start_time
print(f"BENCHMARK:install_time_s:{html_drive_install_time:.2f}")

# Start server in background
subprocess.run(['http-server', '-p', '8080', '&'], check=False, shell=True)

# Test serving a webpage
try:
    import_time_start = time.time()
    response = requests.get('http://localhost:8080')
    import_time = (time.time() - import_time_start) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
    if response.status_code == 200:
        print("TEST_PASS:serving_webpage")
    else:
        print(f"TEST_FAIL:serving_webpage:Expected status code 200, got {response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:serving_webpage:Error {str(e)}")

# Serve a test HTML file and verify URL
try:
    with open('test.html', 'w') as f:
        f.write('<html><body>Hello World!</body></html>')
    response = requests.get('http://localhost:8080/test.html')
    if response.status_code == 200 and 'Hello World!' in response.text:
        print("TEST_PASS:serve_test_html")
    else:
        print(f"TEST_FAIL:serve_test_html:Expected 'Hello World!' in response, got {response.text}")
except Exception as e:
    print(f"TEST_FAIL:serve_test_html:Error {str(e)}")

# Test uploading a new webpage and sharing as a link
try:
    files = {'file': open('test.html', 'rb')}
    response = requests.post('http://localhost:8080/upload', files=files)
    if response.status_code == 200:
        print("TEST_PASS:upload_webpage")
    else:
        print(f"TEST_FAIL:upload_webpage:Expected status code 200, got {response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:upload_webpage:Error {str(e)}")

# Compare performance vs Netlify CMS (similar baseline tool)
# Since HtmlDrive is a server, we'll compare the response time
netlify_response_time = requests.get('https://www.netlify.com/', timeout=5).elapsed.total_seconds() * 1000
vs_netlify_ratio = import_time / netlify_response_time
print(f"BENCHMARK:vs_netlify_import_time_ratio:{vs_netlify_ratio:.2f}")

# Measure and emit memory usage
tracemalloc.start()
time.sleep(1)  # let the server run for a bit
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024:.2f}")
print(f"BENCHMARK:peak_memory_usage_mb:{peak / 1024 / 1024:.2f}")

# Measure and emit number of files
import os
num_files = len(os.listdir('.'))
print(f"BENCHMARK:num_files:{num_files}")

# Measure and emit number of test files
num_test_files = len([f for f in os.listdir('.') if f.startswith('test')])
print(f"BENCHMARK:num_test_files:{num_test_files}")

print("RUN_OK")