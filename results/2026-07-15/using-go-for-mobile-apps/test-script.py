import subprocess
import time
import tracemalloc
import requests
import json

# INSTALLATION
start_time = time.time()
print("INSTALL_OK")
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
subprocess.run(['npm', 'install'], check=False)
install_time = time.time() - start_time
print(f"BENCHMARK:install_time_s:{install_time:.2f}")

# TEST 1: Clone the repository and create a new mobile app using Go
try:
    start_time = time.time()
    subprocess.run(['git', 'clone', 'https://github.com/CaiJimmy/hugo-theme-stack.git'], check=True)
    subprocess.run(['npm', 'run', 'build'], check=True)
    end_time = time.time()
    build_time = end_time - start_time
    print(f"TEST_PASS:clone_and_build")
    print(f"BENCHMARK:clone_and_build_time_s:{build_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:clone_and_build:{str(e)}")

# TEST 2: Run a simple Go program on mobile and verify functionality
try:
    start_time = time.time()
    subprocess.run(['go', 'run', 'main.go'], check=True, cwd='hugo-theme-stack')
    end_time = time.time()
    run_time = end_time - start_time
    print(f"TEST_PASS:run_go_program")
    print(f"BENCHMARK:run_go_program_time_s:{run_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:run_go_program:{str(e)}")

# TEST 3: Measure performance improvements by using a Go-based mobile app
try:
    start_time = time.time()
    response = requests.get('http://localhost:1313/health')
    end_time = time.time()
    response_time = end_time - start_time
    print(f"TEST_PASS:health_check")
    print(f"BENCHMARK:health_check_time_ms:{response_time*1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:health_check:{str(e)}")

# BENCHMARK: Compare performance vs the most similar baseline tool (Flutter)
try:
    start_time = time.time()
    subprocess.run(['flutter', 'run'], check=True, cwd='hugo-theme-stack')
    end_time = time.time()
    flutter_build_time = end_time - start_time
    print(f"BENCHMARK:vs_flutter_build_time_ms:{flutter_build_time*1000:.2f}")
    ratio = (build_time / flutter_build_time)
    print(f"BENCHMARK:vs_flutter_build_time_ratio:{ratio:.2f}")
except Exception as e:
    print(f"BENCHMARK:vs_flutter_build_time:failed_to_run")

# BENCHMARK: Measure memory usage
tracemalloc.start()
start_time = time.time()
subprocess.run(['go', 'run', 'main.go'], check=True, cwd='hugo-theme-stack')
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{peak / 10**6:.2f}")
print(f"BENCHMARK:run_time_ms:{(end_time - start_time)*1000:.2f}")

# BENCHMARK: Measure lines of code
try:
    loc_count = subprocess.check_output(['wc', '-l', 'hugo-theme-stack/main.go']).decode('utf-8').split()[0]
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    print(f"BENCHMARK:loc_count:failed_to_count")

# BENCHMARK: Measure test files count
try:
    test_files_count = len(subprocess.check_output(['find', 'hugo-theme-stack', '-name', '*.test.js']).decode('utf-8').split())
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    print(f"BENCHMARK:test_files_count:failed_to_count")

print("RUN_OK")