import os
import sys
import time
import tracemalloc
import subprocess

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        subprocess.run(['pip', 'install', 'glm-5.1'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/glm-5.1/glm-5.1.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './glm-5.1'], check=True)
            print("INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:{e}")

def test_install():
    try:
        import glm_5_1
        print("TEST_PASS:install_test")
    except ImportError as e:
        print(f"TEST_FAIL:install_test:{e}")

def test_long_horizon_task():
    try:
        import glm_5_1
        start_time = time.time()
        glm_5_1.run_long_horizon_task()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:long_horizon_task_latency_ms:{latency:.2f}")
        print("TEST_PASS:long_horizon_task_test")
    except Exception as e:
        print(f"TEST_FAIL:long_horizon_task_test:{e}")

def test_import_time():
    try:
        start_time = time.time()
        import glm_5_1
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print("TEST_PASS:import_time_test")
    except Exception as e:
        print(f"TEST_FAIL:import_time_test:{e}")

def test_latency_and_throughput():
    try:
        import glm_5_1
        import langchain
        start_time = time.time()
        glm_5_1.run_long_horizon_task()
        end_time = time.time()
        glm_latency = (end_time - start_time) * 1000
        start_time = time.time()
        langchain.run_long_horizon_task()
        end_time = time.time()
        langchain_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_langchain_latency_ratio:{glm_latency / langchain_latency:.2f}")
        print(f"BENCHMARK:vs_langchain_latency_ms:{langchain_latency:.2f}")
        print("TEST_PASS:latency_and_throughput_test")
    except Exception as e:
        print(f"TEST_FAIL:latency_and_throughput_test:{e}")

def test_memory_usage():
    try:
        tracemalloc.start()
        import glm_5_1
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_bytes:{current}")
        print("TEST_PASS:memory_usage_test")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage_test:{e}")

def test_file_count():
    try:
        import os
        file_count = len(os.listdir('.'))
        print(f"BENCHMARK:file_count:{file_count}")
        print("TEST_PASS:file_count_test")
    except Exception as e:
        print(f"TEST_FAIL:file_count_test:{e}")

install_dependencies()
test_install()
test_long_horizon_task()
test_import_time()
test_latency_and_throughput()
test_memory_usage()
test_file_count()
print("RUN_OK")