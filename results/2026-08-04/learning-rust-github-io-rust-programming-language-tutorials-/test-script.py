import subprocess
import time
import tracemalloc
import os
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)

print('INSTALL_OK')

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/Learning-Rust/Learning-Rust.github.io.git'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')
    sys.exit(1)

# Build from source
try:
    start_time = time.time()
    subprocess.run(['cargo', 'build'], cwd='Learning-Rust.github.io', check=True)
    end_time = time.time()
    print(f'BENCHMARK:compile_time_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:build')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:build:{e}')

# Run hello world example
try:
    start_time = time.time()
    subprocess.run(['cargo', 'run'], cwd='Learning-Rust.github.io', check=True)
    end_time = time.time()
    print(f'BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:hello_world')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:hello_world:{e}')

# Measure memory usage
tracemalloc.start()
try:
    subprocess.run(['cargo', 'run'], cwd='Learning-Rust.github.io', check=True)
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:memory_measurement:{e}')
    tracemalloc.stop()
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_mb:{peak / (1024 * 1024)}')
tracemalloc.stop()

# Test documentation generation
try:
    subprocess.run(['cargo', 'doc'], cwd='Learning-Rust.github.io', check=True)
    print('TEST_PASS:docs')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:docs:{e}')

# Compare with baseline tool (Python)
start_time = time.time()
subprocess.run(['python', '-c', 'print("Hello, World!")'], check=True)
end_time = time.time()
python_time = (end_time - start_time) * 1000

start_time = time.time()
subprocess.run(['cargo', 'run'], cwd='Learning-Rust.github.io', check=True)
end_time = time.time()
rust_time = (end_time - start_time) * 1000

ratio = rust_time / python_time
print(f'BENCHMARK:vs_python_helloworld_ratio:{ratio}')

# Print file count and line count
file_count = sum(os.path.isfile(os.path.join(root, file)) for root, _, files in os.walk('Learning-Rust.github.io') for file in files)
print(f'BENCHMARK:file_count:{file_count}')

loc_count = sum(1 for root, _, files in os.walk('Learning-Rust.github.io') for file in files if file.endswith('.rs') for line in open(os.path.join(root, file), 'r'))
print(f'BENCHMARK:loc_count:{loc_count}')

print('RUN_OK')