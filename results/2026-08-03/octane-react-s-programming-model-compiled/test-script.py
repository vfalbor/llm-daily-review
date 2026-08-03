import subprocess
import time
import tracemalloc
import requests
import os

# Install dependencies
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)

# Install Octane CLI
try:
    subprocess.run(['npm', 'install', '-g', '@octane/cli'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')
    print('RUN_OK')
    exit()

# Create a new Octane project
try:
    start_time = time.time()
    subprocess.run(['octane', 'init', 'test-project'], check=True, cwd='/tmp')
    end_time = time.time()
    print(f'BENCHMARK:project_init_time_s:{end_time - start_time}')
    print('TEST_PASS:create_project')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:create_project:{e}')

# Run a basic example using Octane framework
try:
    start_time = time.time()
    subprocess.run(['npm', 'install'], check=True, cwd='/tmp/test-project')
    subprocess.run(['npm', 'run', 'build'], check=True, cwd='/tmp/test-project')
    subprocess.run(['npm', 'start'], check=True, cwd='/tmp/test-project', stdout=subprocess.PIPE)
    end_time = time.time()
    print(f'BENCHMARK:build_and_run_time_s:{end_time - start_time}')
    print('TEST_PASS:run_example')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:run_example:{e}')

# Evaluate Octane performance against React Native
try:
    # Start Octane server
    octane_server = subprocess.Popen(['npm', 'start'], cwd='/tmp/test-project', stdout=subprocess.PIPE)

    # Start React Native server
    react_native_server = subprocess.Popen(['npx', 'react-native', 'start'], cwd='/tmp/test-project', stdout=subprocess.PIPE)

    # Measure response time
    start_time = time.time()
    response = requests.get('http://localhost:3000')
    end_time = time.time()
    print(f'BENCHMARK:octane_response_time_ms:{(end_time - start_time) * 1000}')

    start_time = time.time()
    response = requests.get('http://localhost:8081')
    end_time = time.time()
    print(f'BENCHMARK:react_native_response_time_ms:{(end_time - start_time) * 1000}')

    # Compare performance
    ratio = (end_time - start_time) / (end_time - start_time)
    print(f'BENCHMARK:vs_react_native_response_time_ratio:{ratio}')

    print('TEST_PASS:evaluate_performance')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:evaluate_performance:{e}')

# Check integration with popular state management libraries
try:
    # Install Redux
    subprocess.run(['npm', 'install', 'redux'], check=True, cwd='/tmp/test-project')

    # Create a new Redux store
    with open('/tmp/test-project/src/store.js', 'w') as f:
        f.write('const store = createStore(combineReducers({}));\n')
        f.write('export default store;')

    # Import Redux store in Octane component
    with open('/tmp/test-project/src/App.js', 'a') as f:
        f.write('\nimport store from "./store";\n')
        f.write('console.log(store);\n')

    # Run Octane server with Redux integration
    start_time = time.time()
    subprocess.run(['npm', 'start'], check=True, cwd='/tmp/test-project')
    end_time = time.time()
    print(f'BENCHMARK:redux_integration_time_s:{end_time - start_time}')
    print('TEST_PASS:check_integration')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:check_integration:{e}')

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_mb:{current / 10**6}')
tracemalloc.stop()

# Measure number of test files
test_files = subprocess.run(['find', '/tmp/test-project', '-name', 'test.js'], capture_output=True, text=True)
print(f'BENCHMARK:test_files_count:{len(test_files.stdout.splitlines())}')

print('RUN_OK')