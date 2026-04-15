import subprocess
import importlib
import time
import tracemalloc
import sys

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', 'deps'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/calpaterson/deps.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './deps'], check=False, cwd='./deps')
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL: {str(e)}")

def test_deps_library():
    try:
        start_time = time.time()
        import deps
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time}")
        deps.cooldowns()
        end_time = time.time()
        latency = (end_time - start_time) * 1000 - import_time
        print(f"BENCHMARK:cooldown_latency_ms:{latency}")
        print(f"TEST_PASS:cooldown")
    except Exception as e:
        print(f"TEST_FAIL:cooldown:{str(e)}")

def test_pip_baseline():
    try:
        start_time = time.time()
        subprocess.run(['pip', 'install', 'requests'], check=False)
        end_time = time.time()
        baseline_latency = (end_time - start_time) * 1000
        start_time = time.time()
        import deps
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        ratio = import_time / baseline_latency
        print(f"BENCHMARK:vs_pip_import_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:baseline:{str(e)}")

def benchmark_memory():
    try:
        tracemalloc.start()
        import deps
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memoryPeakBytes:{peak}")
    except Exception as e:
        print(f"TEST_FAIL:memory:{str(e)}")

def main():
    install_dependencies()
    test_deps_library()
    test_pip_baseline()
    benchmark_memory()
    print("RUN_OK")

if __name__ == "__main__":
    main()