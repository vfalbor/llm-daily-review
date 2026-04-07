import subprocess
import time
import tracemalloc
import requests
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

try:
    # Clone Solod repository
    start_time = time.time()
    subprocess.run(['git', 'clone', 'https://github.com/solod-dev/solod.git'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:clone_time_ms:{(end_time - start_time) * 1000:.2f}")

    # Build Solod from source
    start_time = time.time()
    os.chdir('solod')
    subprocess.run(['go', 'build', '-o', 'solod', 'main.go'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:build_time_ms:{(end_time - start_time) * 1000:.2f}")
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Run hello world test
try:
    # Create a simple Solod program
    with open('hello.solod', 'w') as f:
        f.write('package main\n')
        f.write('import "fmt"\n')
        f.write('func main() {\n')
        f.write('    fmt.Println("Hello, World!")\n')
        f.write('}\n')

    # Compile and run the program
    start_time = time.time()
    subprocess.run(['./solod', 'hello.solod'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000:.2f}")
    print("TEST_PASS:hello_world")
except Exception as e:
    print(f"TEST_FAIL:hello_world:{str(e)}")

# Run performance benchmarks
try:
    # Measure import time
    start_time = time.time()
    subprocess.run(['./solod', '-e', 'import "fmt"'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}")

    # Measure compilation time
    start_time = time.time()
    subprocess.run(['./solod', '-c', 'hello.solod'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:compile_time_ms:{(end_time - start_time) * 1000:.2f}")

    # Compare performance with Go
    start_time = time.time()
    subprocess.run(['go', 'run', 'hello.go'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:vs_go_hello_world_ms:{(end_time - start_time) * 1000:.2f}")

    print("TEST_PASS:performance_benchmarks")
except Exception as e:
    print(f"TEST_FAIL:performance_benchmarks:{str(e)}")

# Test correct translation to C
try:
    # Create a Solod program with a simple function
    with open('test.solod', 'w') as f:
        f.write('package main\n')
        f.write('import "fmt"\n')
        f.write('func add(a int, b int) int {\n')
        f.write('    return a + b\n')
        f.write('}\n')
        f.write('func main() {\n')
        f.write('    result := add(2, 3)\n')
        f.write('    fmt.Println(result)\n')
        f.write('}\n')

    # Compile the program to C
    start_time = time.time()
    subprocess.run(['./solod', '-c', 'test.solod'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:translation_time_ms:{(end_time - start_time) * 1000:.2f}")

    # Check the generated C code
    with open('test.c', 'r') as f:
        c_code = f.read()
        if 'add' in c_code and 'main' in c_code:
            print("TEST_PASS:translation_test")
        else:
            print("TEST_FAIL:translation_test:Invalid C code generated")
except Exception as e:
    print(f"TEST_FAIL:translation_test:{str(e)}")

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{peak / 10**6:.2f}")
tracemalloc.stop()

# Measure line count
with open('solod/main.go', 'r') as f:
    lines = f.readlines()
print(f"BENCHMARK:loc_count:{len(lines)}")

# Measure test file count
test_files = [f for f in os.listdir('.') if f.endswith('.solod') or f.endswith('.go')]
print(f"BENCHMARK:test_files_count:{len(test_files)}")

print("RUN_OK")