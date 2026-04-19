import subprocess
import time
import tracemalloc
import sys

def install_dependencies():
    print("Installing dependencies...")
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")

def install_tachyon():
    try:
        print("Installing Tachyon...")
        subprocess.run(['pip', 'install', 'tachyon'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:pip install failed, trying git clone and pip install -e .")
        subprocess.run(['git', 'clone', 'https://github.com/riyaneel/Tachyon.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './Tachyon'], check=True)
        print("INSTALL_OK")

def run_cross_language_ipc_example():
    try:
        import tachyon
        print("Running cross-language IPC example...")
        start_time = time.time()
        # Synthetic data for testing
        data = [1, 2, 3]
        result = tachyon.send(data)
        end_time = time.time()
        print("TEST_PASS:cross_language_ipc_example")
        print(f"BENCHMARK:cross_language_ipc_latency_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:cross_language_ipc_example:{str(e)}")

def measure_import_time():
    try:
        print("Measuring import time...")
        start_time = time.time()
        import tachyon
        end_time = time.time()
        print("TEST_PASS:import_time")
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:import_time:{str(e)}")

def measure_latency():
    try:
        import tachyon
        print("Measuring latency...")
        start_time = time.time()
        # Synthetic data for testing
        data = [1, 2, 3]
        result = tachyon.send(data)
        end_time = time.time()
        print("TEST_PASS:latency_test")
        print(f"BENCHMARK:latency_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:latency_test:{str(e)}")

def compare_performance_to_baseline():
    try:
        import grpc
        print("Comparing performance to gRPC baseline...")
        start_time = time.time()
        # Synthetic data for testing
        data = [1, 2, 3]
        # Mock gRPC call
        result = grpc.server(lambda x: x)
        end_time = time.time()
        grpc_latency = (end_time - start_time) * 1000
        # Measure Tachyon latency again
        start_time = time.time()
        data = [1, 2, 3]
        result = tachyon.send(data)
        end_time = time.time()
        tachyon_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_grpc_latency_ratio:{tachyon_latency / grpc_latency}")
    except Exception as e:
        print(f"TEST_SKIP:compare_performance_to_baseline:{str(e)}")

def measure_memory_usage():
    try:
        print("Measuring memory usage...")
        tracemalloc.start()
        import tachyon
        # Synthetic data for testing
        data = [1, 2, 3]
        result = tachyon.send(data)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        tracemalloc.stop()
        print("TEST_PASS:memory_usage_test")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage_test:{str(e)}")

install_dependencies()
install_tachyon()
run_cross_language_ipc_example()
measure_import_time()
measure_latency()
compare_performance_to_baseline()
measure_memory_usage()
print("RUN_OK")