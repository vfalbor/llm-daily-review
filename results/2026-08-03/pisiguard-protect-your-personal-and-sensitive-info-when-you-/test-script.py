import subprocess
import time
import tracemalloc
import os
import importlib.util

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    try:
        subprocess.run(['pip', 'install', 'PISIGuard'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        subprocess.run(['git', 'clone', 'https://github.com/mohamed--abdel-maksoud/pisiguard.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './pisiguard'], cwd='./pisiguard', check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_pisiguard_data_protection():
    try:
        import PISIGuard
        # Minimal functional test with synthetic data
        start_time = time.time()
        PISIGuard.protect_data("synthetic data")
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:protect_data_ms:{latency:.2f}")
        print("TEST_PASS:test_pisiguard_data_protection")
    except Exception as e:
        print(f"TEST_FAIL:test_pisiguard_data_protection:{str(e)}")

def test_pisiguard_performance():
    try:
        import PISIGuard
        import time
        import tracemalloc
        tracemalloc.start()
        start_time = time.time()
        PISIGuard.evaluate_performance()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        latency = (end_time - start_time) * 1000
        memory_usage = current / 10**6
        print(f"BENCHMARK:evaluate_performance_ms:{latency:.2f}")
        print(f"BENCHMARK:evaluate_performance_memory_mb:{memory_usage:.2f}")
        print("TEST_PASS:test_pisiguard_performance")
    except Exception as e:
        print(f"TEST_FAIL:test_pisiguard_performance:{str(e)}")

def test_pisiguard_integration():
    try:
        import PISIGuard
        import time
        start_time = time.time()
        PISIGuard.check_integration()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:check_integration_ms:{latency:.2f}")
        print("TEST_PASS:test_pisiguard_integration")
    except Exception as e:
        print(f"TEST_FAIL:test_pisiguard_integration:{str(e)}")

def compare_performance():
    try:
        import PISIGuard
        import Privacy_Guardian
        import time
        start_time = time.time()
        PISIGuard.evaluate_performance()
        end_time = time.time()
        pisiguard_latency = (end_time - start_time) * 1000
        start_time = time.time()
        Privacy_Guardian.evaluate_performance()
        end_time = time.time()
        privacy_guardian_latency = (end_time - start_time) * 1000
        ratio = pisiguard_latency / privacy_guardian_latency
        print(f"BENCHMARK:vs_privacy_guardian_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"BENCHMARK:vs_privacy_guardian_ratio:NA")

def import_time_benchmark():
    try:
        start_time = time.time()
        import PISIGuard
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
    except Exception as e:
        print(f"BENCHMARK:import_time_ms:NA")

def loc_count_benchmark():
    try:
        import os
        loc_count = 0
        for root, dirs, files in os.walk('./pisiguard'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        loc_count += len(f.readlines())
        print(f"BENCHMARK:loc_count:{loc_count}")
    except Exception as e:
        print(f"BENCHMARK:loc_count:NA")

def test_files_count_benchmark():
    try:
        import os
        test_files_count = 0
        for root, dirs, files in os.walk('./pisiguard'):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files_count += 1
        print(f"BENCHMARK:test_files_count:{test_files_count}")
    except Exception as e:
        print(f"BENCHMARK:test_files_count:NA")

def main():
    install_dependencies()
    import_time_benchmark()
    test_pisiguard_data_protection()
    test_pisiguard_performance()
    test_pisiguard_integration()
    compare_performance()
    loc_count_benchmark()
    test_files_count_benchmark()
    print("RUN_OK")

if __name__ == "__main__":
    main()