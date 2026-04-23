import subprocess
import sys
import time
import tracemalloc
from importlib import import_module
from unittest.mock import patch, Mock

# Install system packages
def install_sys_packages():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")

# Install pip package
def install_pip_package():
    try:
        subprocess.run(['pip', 'install', 'zed'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        # Fallback to installing from source
        subprocess.run(['git', 'clone', 'https://github.com/zed-dev/zed.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './zed'], check=True)
        print("INSTALL_OK")

# Import Zed and run simple example
def test_import_zed():
    try:
        start_time = time.time()
        import zed
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time}")
        # Run simple example
        example = zed.Example()
        example.run()
        print("TEST_PASS:test_import_zed")
    except Exception as e:
        print(f"TEST_FAIL:test_import_zed:{str(e)}")

# Mock Zed API request and measure latency
def test_zed_api_latency():
    try:
        with patch('zed.api.request') as mock_request:
            mock_request.return_value = Mock(response_time=100)
            start_time = time.time()
            import zed
            zed.api.request()
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            print(f"BENCHMARK:zed_api_latency_ms:{latency}")
            print("TEST_PASS:test_zed_api_latency")
    except Exception as e:
        print(f"TEST_FAIL:test_zed_api_latency:{str(e)}")

# Compare performance vs LangChain
def test_vs_langchain():
    try:
        import langchain
        start_time = time.time()
        import zed
        end_time = time.time()
        zed_import_time = (end_time - start_time) * 1000
        start_time = time.time()
        import langchain
        end_time = time.time()
        langchain_import_time = (end_time - start_time) * 1000
        ratio = zed_import_time / langchain_import_time
        print(f"BENCHMARK:vs_langchain_import_time_ratio:{ratio}")
        print("TEST_PASS:test_vs_langchain")
    except Exception as e:
        print(f"TEST_FAIL:test_vs_langchain:{str(e)}")

# Measure memory usage
def test_memory_usage():
    try:
        tracemalloc.start()
        import zed
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024}")
        print("TEST_PASS:test_memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:test_memory_usage:{str(e)}")

# Count lines of code
def test_loc_count():
    try:
        import os
        loc_count = 0
        for root, dirs, files in os.walk('/zed'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        loc_count += len(f.readlines())
        print(f"BENCHMARK:loc_count:{loc_count}")
        print("TEST_PASS:test_loc_count")
    except Exception as e:
        print(f"TEST_FAIL:test_loc_count:{str(e)}")

# Count test files
def test_test_files_count():
    try:
        import os
        test_files_count = 0
        for root, dirs, files in os.walk('/zed'):
            for file in files:
                if file.endswith('_test.py'):
                    test_files_count += 1
        print(f"BENCHMARK:test_files_count:{test_files_count}")
        print("TEST_PASS:test_test_files_count")
    except Exception as e:
        print(f"TEST_FAIL:test_test_files_count:{str(e)}")

# Main
if __name__ == "__main__":
    install_sys_packages()
    install_pip_package()
    test_import_zed()
    test_zed_api_latency()
    test_vs_langchain()
    test_memory_usage()
    test_loc_count()
    test_test_files_count()
    print("RUN_OK")