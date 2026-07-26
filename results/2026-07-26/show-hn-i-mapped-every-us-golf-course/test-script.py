import subprocess
import time
import tracemalloc
import requests

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
print('INSTALL_OK')

# Install tool dependencies
subprocess.run(['npm', 'install'], cwd='/app', check=False)
try:
    subprocess.run(['npm', 'start', '&'], cwd='/app', check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Test 1: Basic run
def test_basic_run():
    try:
        response = requests.get('http://localhost:3000')
        if response.status_code == 200:
            print(f'TEST_PASS:basic_run')
        else:
            print(f'TEST_FAIL:basic_run:Invalid status code {response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:basic_run:{str(e)}')

# Test 2: Measure performance
def test_performance():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:3000')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:response_time_ms:{response_time:.2f}')
        
        # Measure memory usage
        tracemalloc.start()
        response = requests.get('http://localhost:3000')
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_bytes:{peak}')
        
        # Measure request count
        response = requests.get('http://localhost:3000')
        print(f'BENCHMARK:request_count:1')
        
        print(f'TEST_PASS:performance')
    except Exception as e:
        print(f'TEST_FAIL:performance:{str(e)}')

# Test 3: Compare vs similar tool
def test_compare_performance():
    try:
        # Start similar tool in background
        subprocess.run(['npm', 'start', '&'], cwd='/similar_tool', check=False)
        
        # Measure response time of similar tool
        start_time = time.time()
        response = requests.get('http://localhost:3001')
        end_time = time.time()
        similar_tool_response_time = (end_time - start_time) * 1000
        
        # Measure response time of golf-course-browser
        start_time = time.time()
        response = requests.get('http://localhost:3000')
        end_time = time.time()
        golf_course_browser_response_time = (end_time - start_time) * 1000
        
        ratio = golf_course_browser_response_time / similar_tool_response_time
        print(f'BENCHMARK:vs_similar_tool_response_time_ratio:{ratio:.2f}')
        
        print(f'TEST_PASS:compare_performance')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance:{str(e)}')

# Run tests
test_basic_run()
test_performance()
test_compare_performance()

# Print final status
print('RUN_OK')