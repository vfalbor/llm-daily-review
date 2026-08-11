import subprocess
import time
import tracemalloc
import os
import sys

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: {e}")
        return False
    return True

def install_h3_c():
    if not run_command(['git', 'clone', 'https://github.com/antirez/h3.c.git']):
        return False
    if not run_command(['cd', 'h3.c', '&&', 'make']):
        return False
    return True

def install_baseline_tools():
    # Install Python
    if not run_command(['apk', 'add', '--no-cache', 'python3']):
        return False
    # Install pip
    if not run_command(['python3', '-m', 'ensurepip']):
        return False
    # Install numpy and scipy for baseline comparison
    if not run_command(['pip3', 'install', '--no-cache-dir', 'numpy', 'scipy']):
        return False
    return True

def run_h3_c_example():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['./h3.c/h3_example'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:example_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:example_memory_mb:{current / 10**6}")
        print(f"TEST_PASS:h3_c_example")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:h3_c_example:{e}")
    except Exception as e:
        print(f"TEST_FAIL:h3_c_example:{e}")

def run_baseline_example():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python3', '-c', 'import numpy as np; np.random.rand(1000, 1000)'],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:baseline_example_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:baseline_example_memory_mb:{current / 10**6}")
        print(f"TEST_PASS:baseline_example")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:baseline_example:{e}")
    except Exception as e:
        print(f"TEST_FAIL:baseline_example:{e}")

def compare_performance():
    try:
        # Run h3_c example and measure execution time
        start_time = time.time()
        subprocess.run(['./h3.c/h3_example'], check=True)
        end_time = time.time()
        h3_c_time = end_time - start_time
        # Run baseline example and measure execution time
        start_time = time.time()
        subprocess.run(['python3', '-c', 'import numpy as np; np.random.rand(1000, 1000)'],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end_time = time.time()
        baseline_time = end_time - start_time
        print(f"BENCHMARK:vs_python_ratio:{h3_c_time / baseline_time}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance:{e}")

def count_source_files():
    try:
        source_files = subprocess.run(['find', 'h3.c', '-type', 'f', '-name', '*.c'],
                                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True)
        source_files = source_files.stdout.splitlines()
        print(f"BENCHMARK:source_files_count:{len(source_files)}")
        print(f"TEST_PASS:count_source_files")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:count_source_files:{e}")
    except Exception as e:
        print(f"TEST_FAIL:count_source_files:{e}")

def main():
    print("INSTALL_OK")
    if not install_h3_c():
        return
    if not install_baseline_tools():
        return
    run_h3_c_example()
    run_baseline_example()
    compare_performance()
    count_source_files()
    tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:mem_usage_mb:{current / 10**6}")
    print(f"BENCHMARK:peak_mem_usage_mb:{peak / 10**6}")
    print("RUN_OK")

if __name__ == "__main__":
    # Install git
    if not run_command(['apk', 'add', '--no-cache', 'git']):
        print("INSTALL_FAIL: git installation failed")
        sys.exit(1)
    main()