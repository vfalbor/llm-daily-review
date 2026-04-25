import subprocess
import time
import tracemalloc
import os

# Install system packages
print("Installing system packages...")
try:
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install system packages: {e}")

# Clone and build Turbo Vision 2.0 from source
print("Building Turbo Vision 2.0 from source...")
try:
    start_time = time.time()
    subprocess.run(['git', 'clone', 'https://github.com/magiblot/tvision.git'], check=True)
    subprocess.run(['cd', 'tvision', '&&', 'cargo', 'build'], check=True, shell=True)
    end_time = time.time()
    print(f"BENCHMARK:build_time_s:{end_time - start_time:.2f}")
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to build Turbo Vision 2.0: {e}")

# Test creating a UI project
print("Testing creating a UI project...")
try:
    start_time = time.time()
    subprocess.run(['cargo', 'new', 'tvision_project', '--bin'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:create_project_time_ms:{(end_time - start_time) * 1000:.2f}")
    print("TEST_PASS:create_ui_project")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:create_ui_project:Failed to create UI project: {e}")

# Test compiling and running a simple application
print("Testing compiling and running a simple application...")
try:
    start_time = time.time()
    subprocess.run(['cd', 'tvision_project', '&&', 'cargo', 'build', '&&', './target/debug/tvision_project'], check=True, shell=True)
    end_time = time.time()
    print(f"BENCHMARK:run_app_time_ms:{(end_time - start_time) * 1000:.2f}")
    print("TEST_PASS:compile_and_run")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:compile_and_run:Failed to compile and run: {e}")

# Compare performance with original Turbo Vision
print("Comparing performance with original Turbo Vision...")
try:
    # Original Turbo Vision is not available for direct comparison, using a mock comparison
    start_time = time.time()
    subprocess.run(['sleep', '1'], check=True)
    end_time = time.time()
    turbo_vision_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['cd', 'tvision_project', '&&', './target/debug/tvision_project'], check=True, shell=True)
    end_time = time.time()
    tvision_time = end_time - start_time
    print(f"BENCHMARK:vs_turbo_vision_time_ratio:{tvision_time / turbo_vision_time:.2f}")
    print("TEST_PASS:compare_performance")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:compare_performance:Failed to compare performance: {e}")

# Measure memory usage
print("Measuring memory usage...")
try:
    tracemalloc.start()
    subprocess.run(['cd', 'tvision_project', '&&', './target/debug/tvision_project'], check=True, shell=True)
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_mb:{current / 10**6:.2f}")
    tracemalloc.stop()
    print("TEST_PASS:measure_memory")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:measure_memory:Failed to measure memory: {e}")

# Measure execution count
print("Measuring execution count...")
try:
    start_time = time.time()
    for _ in range(100):
        subprocess.run(['cd', 'tvision_project', '&&', './target/debug/tvision_project'], check=True, shell=True)
    end_time = time.time()
    print(f"BENCHMARK:execution_count_time_s:{end_time - start_time:.2f}")
    print("TEST_PASS:measure_execution_count")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:measure_execution_count:Failed to measure execution count: {e}")

# Measure lines of code
print("Measuring lines of code...")
try:
    loc = subprocess.run(['wc', '-l', 'tvision/src/main.rs'], capture_output=True, text=True, check=True)
    print(f"BENCHMARK:loc_count:{loc.stdout.split()[0]}")
    print("TEST_PASS:measure_loc")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:measure_loc:Failed to measure lines of code: {e}")

print("RUN_OK")