import subprocess
import time
import tracemalloc
import importlib.util

def install_htmx():
    try:
        # Try to install via pip
        subprocess.run(['pip', 'install', 'htmx'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        try:
            # Fallback to installing via git clone + pip install -e
            subprocess.run(['git', 'clone', 'https://github.com/bigskysoftware/htmx'], check=True)
            subprocess.run(['pip', 'install', '-e', './htmx'], check=True)
            print("INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:{e}")

def test_import():
    try:
        spec = importlib.util.find_spec("htmx")
        if spec is not None:
            print("TEST_PASS:import_test")
        else:
            print("TEST_FAIL:import_test:htmx module not found")
    except Exception as e:
        print(f"TEST_FAIL:import_test:{e}")

def test_run():
    try:
        # Run a minimal functional test with synthetic data
        import htmx
        htmx.trigger('test', 'test')
        print("TEST_PASS:run_test")
    except Exception as e:
        print(f"TEST_FAIL:run_test:{e}")

def benchmark_import_time():
    try:
        import time
        start_time = time.time()
        import htmx
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:import_benchmark:{e}")

def benchmark_core_operation_latency():
    try:
        import htmx
        import time
        start_time = time.time()
        htmx.trigger('test', 'test')
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:core_operation_latency_ms:{latency:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:core_operation_benchmark:{e}")

def compare_vs_baseline():
    try:
        # Compare performance vs similar baseline tool
        import htmx
        import time
        start_time = time.time()
        htmx.trigger('test', 'test')
        end_time = time.time()
        htmx_latency = (end_time - start_time) * 1000

        # Measure baseline tool latency
        import requests
        start_time = time.time()
        requests.get('https://httpbin.org/get')
        end_time = time.time()
        baseline_latency = (end_time - start_time) * 1000

        ratio = htmx_latency / baseline_latency
        print(f"BENCHMARK:vs_requests_latency_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:compare_vs_baseline:{e}")

def main():
    # Install git package
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)

    # Install htmx package
    install_htmx()

    # Run tests
    test_import()
    test_run()

    # Run benchmarks
    benchmark_import_time()
    benchmark_core_operation_latency()

    # Compare vs baseline
    compare_vs_baseline()

    # Measure memory usage
    tracemalloc.start()
    import htmx
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    tracemalloc.stop()

    # Measure lines of code
    import os
    loc_count = 0
    for root, dirs, files in os.walk('./'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += len(f.readlines())
    print(f"BENCHMARK:loc_count:{loc_count}")

    # Measure test files count
    test_files_count = 0
    for root, dirs, files in os.walk('./'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files_count += 1
    print(f"BENCHMARK:test_files_count:{test_files_count}")

    print("RUN_OK")

if __name__ == "__main__":
    main()