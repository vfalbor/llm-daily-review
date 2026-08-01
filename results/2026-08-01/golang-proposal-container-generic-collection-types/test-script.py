import subprocess
import time
import tracemalloc
import os

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')
    exit(1)

# Install go
try:
    subprocess.run(['go', 'version'], check=True)
except subprocess.CalledProcessError:
    print('INSTALL_FAIL:go not installed')
    exit(1)

# Clone the go repo
start_time = time.time()
try:
    subprocess.run(['git', 'clone', 'https://github.com/golang/go.git'], check=True)
    end_time = time.time()
    install_time = end_time - start_time
    print(f'BENCHMARK:install_time_s:{install_time:.2f}')
    print('TEST_PASS:clone_go_repo')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:clone_go_repo:{e}')
    exit(1)

# Build go from source
start_time = time.time()
try:
    subprocess.run(['cd', 'go', '&&', './make.bash'], check=True, shell=True)
    end_time = time.time()
    build_time = end_time - start_time
    print(f'BENCHMARK:build_time_s:{build_time:.2f}')
    print('TEST_PASS:build_go')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:build_go:{e}')

# Run hello world in go
start_time = time.time()
try:
    with open('hello.go', 'w') as f:
        f.write('package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello World")\n}')
    subprocess.run(['go', 'run', 'hello.go'], check=True)
    end_time = time.time()
    hello_world_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:hello_world_ms:{hello_world_time:.2f}')
    print('TEST_PASS:run_hello_world_go')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:run_hello_world_go:{e}')

# Run hello world in python
start_time = time.time()
try:
    with open('hello.py', 'w') as f:
        f.write('print("Hello World")')
    subprocess.run(['python', 'hello.py'], check=True)
    end_time = time.time()
    hello_world_time_python = (end_time - start_time) * 1000
    print(f'BENCHMARK:hello_world_ms_python:{hello_world_time_python:.2f}')
    print('TEST_PASS:run_hello_world_python')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:run_hello_world_python:{e}')

# Compare performance
if hello_world_time and hello_world_time_python:
    ratio = hello_world_time / hello_world_time_python
    print(f'BENCHMARK:vs_python_hello_world_ratio:{ratio:.2f}')

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024):.2f}')

# Count number of files
file_count = 0
for root, dirs, files in os.walk('.'):
    file_count += len(files)
print(f'BENCHMARK:file_count:{file_count}')

print('RUN_OK')