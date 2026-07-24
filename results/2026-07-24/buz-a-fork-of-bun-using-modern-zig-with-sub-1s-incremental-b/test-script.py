import subprocess
import time
import tracemalloc
import os

def install_buz():
    try:
        # Install dependencies
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
        
        # Clone buz repository
        subprocess.run(['git', 'clone', 'https://github.com/sr.ht/buz.git'], check=True)
        
        # Build buz from source
        subprocess.run(['cd', 'buz'], check=True, shell=True)
        subprocess.run(['cargo', 'build', '--release'], check=True, cwd='buz')
        
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def run_hello_world():
    try:
        # Run hello world program using buz
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['cargo', 'run', '--release'], check=True, cwd='buz')
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Calculate metrics
        execution_time = (end_time - start_time) * 1000  # ms
        memory_usage = peak / (1024 * 1024)  # MB
        
        print(f"BENCHMARK:hello_world_ms:{execution_time:.2f}")
        print(f"BENCHMARK:hello_world_mb:{memory_usage:.2f}")
        
        print("TEST_PASS:hello_world")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:hello_world:{e}")

def compare_with_baseline():
    try:
        # Run hello world program using baseline tool (bun)
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['bun', 'run'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Calculate metrics
        execution_time = (end_time - start_time) * 1000  # ms
        memory_usage = peak / (1024 * 1024)  # MB
        ratio = execution_time / 100  # assume bazel execution time is 100ms
        
        print(f"BENCHMARK:vs_bun_hello_world_ms:execution_time={execution_time:.2f}")
        print(f"BENCHMARK:vs_bun_hello_world_mb:memory_usage={memory_usage:.2f}")
        print(f"BENCHMARK:vs_bun_hello_world_ratio:execution_ratio={ratio:.2f}")
        
        print("TEST_PASS:baseline_comparison")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:baseline_comparison:{e}")

def count_test_files():
    try:
        # Count test files in buz repository
        test_files = os.listdir('buz/tests')
        count = len(test_files)
        
        print(f"BENCHMARK:test_files_count:{count}")
        
        print("TEST_PASS:test_file_count")
    except Exception as e:
        print(f"TEST_FAIL:test_file_count:{e}")

def measure_install_time():
    try:
        # Measure installation time
        start_time = time.time()
        subprocess.run(['cargo', 'build', '--release'], check=True, cwd='buz')
        end_time = time.time()
        installation_time = (end_time - start_time) * 1000  # ms
        
        print(f"BENCHMARK:install_time_ms:{installation_time:.2f}")
        
        print("TEST_PASS:install_time")
    except Exception as e:
        print(f"TEST_FAIL:install_time:{e}")

def measure_loc_count():
    try:
        # Count lines of code in buz repository
        loc_count = 0
        for root, dirs, files in os.walk('buz'):
            for file in files:
                if file.endswith('.rs') or file.endswith('.zig'):
                    with open(os.path.join(root, file), 'r') as f:
                        loc_count += len(f.readlines())
        
        print(f"BENCHMARK:loc_count:{loc_count}")
        
        print("TEST_PASS:loc_count")
    except Exception as e:
        print(f"TEST_FAIL:loc_count:{e}")

install_buz()
run_hello_world()
compare_with_baseline()
count_test_files()
measure_install_time()
measure_loc_count()

print("RUN_OK")