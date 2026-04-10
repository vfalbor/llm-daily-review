import subprocess
import pip
import importlib
import time
import tracemalloc
from marimo_pair import *

def install_marimo_pair():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        subprocess.run(['pip', 'install', 'marimo-pair'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/marimo-team/marimo-pair.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './marimo-pair'], check=True, cwd='./marimo-pair')
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")

def test_marimo_pair():
    start_time = time.time()
    try:
        import marimo_pair
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time}")
        
        tracemalloc.start()
        marimo_pair.run()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_bytes:{current}")
        
        start_time = time.time()
        marimo_pair.run()
        end_time = time.time()
        operation_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:operation_latency_ms:{operation_latency}")
        
        print("TEST_PASS:marimo_pair_interaction")
    except Exception as e:
        print(f"TEST_FAIL:marimo_pair_interaction:{str(e)}")

def compare_baseline():
    try:
        import numpy as np
        start_time = time.time()
        np.random.rand(1000, 1000)
        end_time = time.time()
        numpy_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_numpy_latency_ms:{numpy_latency}")
        
        import marimo_pair
        start_time = time.time()
        marimo_pair.run()
        end_time = time.time()
        marimo_latency = (end_time - start_time) * 1000
        ratio = marimo_latency / numpy_latency
        print(f"BENCHMARK:vs_numpy_latency_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:baseline_comparison:{str(e)}")

def main():
    install_marimo_pair()
    test_marimo_pair()
    compare_baseline()
    print("RUN_OK")

if __name__ == "__main__":
    main()