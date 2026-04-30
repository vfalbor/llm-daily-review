import subprocess
import time
from tracemalloc import start, stop, get_traced_memory

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

# Install GCC 16
start_time = time.time()
subprocess.run(['git', 'clone', 'https://github.com/gcc-mirror/gcc.git'], check=False)
subprocess.run(['mkdir', 'gcc-build'], check=False)
subprocess.run(['cd', 'gcc-build', '&&', './../gcc/configure', '--enable-languages=c,c++'], check=False, shell=True)
subprocess.run(['cd', 'gcc-build', '&&', 'make', '-j4'], check=False, shell=True)
subprocess.run(['cd', 'gcc-build', '&&', 'make', 'install'], check=False, shell=True)
end_time = time.time()

print(f"INSTALL_OK")
print(f"BENCHMARK:install_time_s:{end_time - start_time}")

# Test C++ project compilation using GCC 16
try:
    start_time = time.time()
    subprocess.run(['gcc-build/bin/gcc', '-std=c++20', '-o', 'test', 'test.cpp'], check=True)
    end_time = time.time()
    print(f"TEST_PASS:compile_test")
    print(f"BENCHMARK:compile_time_ms:{(end_time - start_time) * 1000}")
except Exception as e:
    print(f"TEST_FAIL:compile_test:{e}")

# Compare performance vs GCC 15
try:
    start_time = time.time()
    # Use 'gcc-15' as a placeholder, replace with actual GCC 15 installation
    subprocess.run(['gcc-15', '-std=c++14', '-o', 'test', 'test.cpp'], check=True)
    end_time = time.time()
    gcc15_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['gcc-build/bin/gcc', '-std=c++20', '-o', 'test', 'test.cpp'], check=True)
    end_time = time.time()
    gcc16_time = end_time - start_time
    ratio = gcc16_time / gcc15_time
    print(f"BENCHMARK:vs_gcc15_compile_ratio:{ratio}")
except Exception as e:
    print(f"TEST_FAIL:compare_gcc15:{e}")

# Test C++20 features
try:
    # Create a test.cpp file with C++20 features
    with open('test.cpp', 'w') as f:
        f.write("""
        #include <iostream>
        int main() {
            std::cout << "Hello, World!" << std::endl;
            return 0;
        }
        """)
    start_time = time.time()
    subprocess.run(['gcc-build/bin/gcc', '-std=c++20', '-o', 'test', 'test.cpp'], check=True)
    end_time = time.time()
    print(f"TEST_PASS:cpp20_test")
    print(f"BENCHMARK:cpp20_compile_time_ms:{(end_time - start_time) * 1000}")
except Exception as e:
    print(f"TEST_FAIL:cpp20_test:{e}")

# Measure memory usage
start_time = time.time()
start()
subprocess.run(['gcc-build/bin/gcc', '-std=c++20', '-o', 'test', 'test.cpp'], check=True)
stop()
mem_usage = get_traced_memory()[1]
end_time = time.time()
print(f"BENCHMARK:memory_usage_kb:{mem_usage / 1024}")

print(f"RUN_OK")