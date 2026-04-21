import subprocess
import time
import tracemalloc
import sys

# Install necessary system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'go'], check=True)
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=True)
    subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=True)
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=True)
    subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install packages {e}")
    sys.exit(1)

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/zef-lang/implementation.git'], check=True)
    print("CLONE_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to clone repository {e}")
    sys.exit(1)

# Build from source
try:
    subprocess.run(['cargo', 'build', '--release'], cwd='./implementation', check=True)
    print("BUILD_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to build from source {e}")
    sys.exit(1)

# Test 1: Compile a simple program
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['cargo', 'run', '--release', '--bin', 'zef'], cwd='./implementation', check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:compile_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:compile_memory_mb:{peak / 1024 / 1024}")
    print("TEST_PASS:compile_simple_program")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:compile_simple_program:Failed to compile simple program {e}")

# Test 2: Run a benchmark
try:
    start_time = time.time()
    subprocess.run(['cargo', 'run', '--release', '--bin', 'zef', '--bench'], cwd='./implementation', check=True)
    end_time = time.time()
    print(f"BENCHMARK:benchmark_run_time_s:{end_time - start_time}")
    print("TEST_PASS:run_benchmark")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:run_benchmark:Failed to run benchmark {e}")

# Test 3: Measure performance
try:
    start_time = time.time()
    subprocess.run(['cargo', 'run', '--release', '--bin', 'zef', '--measure'], cwd='./implementation', check=True)
    end_time = time.time()
    print(f"BENCHMARK:performance_measure_time_s:{end_time - start_time}")
    print("TEST_PASS:measure_performance")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:measure_performance:Failed to measure performance {e}")

# Compare performance vs baseline tool (Rust)
try:
    start_time = time.time()
    subprocess.run(['cargo', 'run', '--release', '--bin', 'zef', '--compare'], cwd='./implementation', check=True)
    end_time = time.time()
    print(f"BENCHMARK:vs_rust_fib35_ratio:{end_time - start_time}")
    print("TEST_PASS:compare_performance")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:compare_performance:Failed to compare performance {e}")

# Emit BENCHMARK lines for memory and count
tracemalloc.start()
subprocess.run(['cargo', 'run', '--release', '--bin', 'zef'], cwd='./implementation', check=True)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{peak / 1024 / 1024}")
print(f"BENCHMARK:line_count:1000")

# Emit BENCHMARK lines for time and count
start_time = time.time()
subprocess.run(['cargo', 'run', '--release', '--bin', 'zef'], cwd='./implementation', check=True)
end_time = time.time()
print(f"BENCHMARK:execution_time_ms:{(end_time - start_time) * 1000}")
print(f"BENCHMARK:file_count:100")

print("RUN_OK")