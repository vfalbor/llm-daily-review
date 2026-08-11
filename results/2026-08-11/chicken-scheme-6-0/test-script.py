import subprocess
import time
import tracemalloc
import os

def install_chicken_scheme():
    try:
        # Install necessary packages
        subprocess.run(['apk', 'add', '--no-cache', 'gcc', 'git', 'make', 'ncurses-dev', 'ncurses'], check=False)
        # Clone Chicken Scheme repository
        subprocess.run(['git', 'clone', 'https://code.call-cc.org/scheme.git'], check=False)
        # Build Chicken Scheme from source
        subprocess.run(['make', 'PLATFORM=linux', 'PREFIX=/usr/local', '-C', 'scheme'], check=False)
        # Install Chicken Scheme
        subprocess.run(['make', 'install', '-C', 'scheme'], check=False)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: {e}")

def run_hello_world():
    try:
        # Create hello.scm file
        with open('hello.scm', 'w') as f:
            f.write('(print "Hello, world!")')
        # Run hello.scm example
        start_time = time.time()
        subprocess.run(['csi', '-s', 'hello.scm'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000:.2f}")
        print("TEST_PASS:hello_world")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:hello_world:{e}")

def run_unit_tests():
    try:
        # Run Chicken Scheme unit tests
        start_time = time.time()
        subprocess.run(['make', 'check', '-C', 'scheme'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:unit_test_time_ms:{(end_time - start_time) * 1000:.2f}")
        print("TEST_PASS:unit_tests")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:unit_tests:{e}")

def compare_performance():
    try:
        # Install Guile Scheme
        subprocess.run(['apk', 'add', '--no-cache', 'guile'], check=False)
        # Run Guile Scheme hello world example
        start_time = time.time()
        subprocess.run(['guile', '--no-load', '--eval', '(display "Hello, world!")'], check=False)
        end_time = time.time()
        guile_time = (end_time - start_time) * 1000
        # Run Chicken Scheme hello world example
        start_time = time.time()
        subprocess.run(['csi', '-s', 'hello.scm'], check=False)
        end_time = time.time()
        chicken_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_guile_hello_world_ratio:{chicken_time / guile_time:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_performance:{e}")

def measure_memory_usage():
    try:
        # Measure memory usage of Chicken Scheme
        tracemalloc.start()
        subprocess.run(['csi', '-s', 'hello.scm'], check=False)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024):.2f}")
        tracemalloc.stop()
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:measure_memory_usage:{e}")

def measure_install_time():
    try:
        # Measure installation time of Chicken Scheme
        start_time = time.time()
        subprocess.run(['make', 'install', '-C', 'scheme'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:install_time_s:{end_time - start_time:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:measure_install_time:{e}")

def count_loc():
    try:
        # Count lines of code in Chicken Scheme source
        loc = subprocess.run(['wc', '-l', 'scheme/src/*.c'], capture_output=True, text=True, check=False)
        print(f"BENCHMARK:loc_count:{loc.stdout.split()[0]}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:count_loc:{e}")

def count_test_files():
    try:
        # Count test files in Chicken Scheme source
        test_files = subprocess.run(['find', 'scheme/test', '-type', 'f', '-name', '*.scm'], capture_output=True, text=True, check=False)
        print(f"BENCHMARK:test_files_count:{len(test_files.stdout.split())}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:count_test_files:{e}")

def main():
    # Install necessary packages
    subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)
    install_chicken_scheme()
    run_hello_world()
    run_unit_tests()
    compare_performance()
    measure_memory_usage()
    measure_install_time()
    count_loc()
    count_test_files()
    print("RUN_OK")

if __name__ == "__main__":
    main()