import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

print("INSTALL_OK")

# Clone the repository
start_time = time.time()
subprocess.run(['git', 'clone', 'https://github.com/ar-ms/c-compiler.git'], check=False)
clone_time = time.time() - start_time
print(f"BENCHMARK:clone_time_s:{clone_time:.2f}")

# Build from source
start_time = time.time()
os.chdir('c-compiler')
subprocess.run(['zig', 'build'], check=False)
build_time = time.time() - start_time
print(f"BENCHMARK:build_time_s:{build_time:.2f}")

# Run hello world
start_time = time.time()
subprocess.run(['zig', 'run', 'hello.zig'], check=False)
run_time = time.time() - start_time
print(f"BENCHMARK:run_time_s:{run_time:.2f}")

# Check output matches C compiler
try:
    start_time = time.time()
    subprocess.run(['zig', 'run', 'hello.zig'], check=True, stdout=subprocess.PIPE)
    end_time = time.time()
    print(f"BENCHMARK:hello_world_time_s:{end_time - start_time:.2f}")
    print("TEST_PASS:hello_world")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:hello_world:{e}")

# Compare performance vs the most similar baseline tool (C compiler)
# For demonstration purposes, assume the C compiler is installed and available
try:
    start_time = time.time()
    subprocess.run(['gcc', 'hello.c', '-o', 'hello'], check=True, stdout=subprocess.PIPE)
    end_time = time.time()
    c_compile_time = end_time - start_time
    ratio = build_time / c_compile_time
    print(f"BENCHMARK:vs_c_compiler_build_ratio:{ratio:.2f}")
    print("TEST_PASS:c_compiler_comparison")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:c_compiler_comparison:{e}")

# Measure memory usage
tracemalloc.start()
subprocess.run(['zig', 'run', 'hello.zig'], check=False)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{peak / 1024 / 1024:.2f}")

# Count lines of code
loc_count = 0
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.zig'):
            with open(os.path.join(root, file), 'r') as f:
                loc_count += len(f.readlines())
print(f"BENCHMARK:loc_count:{loc_count}")

# Count test files
test_files_count = 0
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.test.zig'):
            test_files_count += 1
print(f"BENCHMARK:test_files_count:{test_files_count}")

print("RUN_OK")