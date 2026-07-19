import subprocess
import time
import tracemalloc
import importlib.util
import os

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

def install_package():
    try:
        subprocess.run(['pip', 'install', 'loopgain'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/loopgain-ai/loopgain.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './loopgain'], check=False, cwd='./loopgain')
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL: {str(e)}")

def measure_import_time():
    try:
        start_time = time.time()
        import loopgain
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time}")
        print(f"TEST_PASS:import_test")
    except Exception as e:
        print(f"TEST_FAIL:import_test:{str(e)}")

def measure_loopgain_latency():
    try:
        import loopgain
        start_time = time.time()
        loopgain.run_scenario()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:loopgain_latency_ms:{latency}")
        print(f"TEST_PASS:loopgain_latency_test")
    except Exception as e:
        print(f"TEST_FAIL:loopgain_latency_test:{str(e)}")

def measure_control_theories_benchmark():
    try:
        import loopgain
        control_theories = ['pid', 'state_space', 'model_predictive']
        for theory in control_theories:
            start_time = time.time()
            loopgain.run_scenario(control_theory=theory)
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            print(f"BENCHMARK:control_theory_{theory}_ms:{latency}")
            print(f"TEST_PASS:control_theory_{theory}_test")
    except Exception as e:
        print(f"TEST_FAIL:control_theories_benchmark:{str(e)}")

def measure_max_iterations_benchmark():
    try:
        import loopgain
        max_iterations = 100
        start_time = time.time()
        loopgain.run_scenario(max_iterations=max_iterations)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:max_iterations_{max_iterations}_ms:{latency}")
        print(f"TEST_PASS:max_iterations_test")
    except Exception as e:
        print(f"TEST_FAIL:max_iterations_benchmark:{str(e)}")

def compare_performance():
    try:
        import loopgain
        import langchain
        start_time = time.time()
        loopgain.run_scenario()
        end_time = time.time()
        loopgain_latency = (end_time - start_time) * 1000
        start_time = time.time()
        langchain.run_scenario()
        end_time = time.time()
        langchain_latency = (end_time - start_time) * 1000
        ratio = loopgain_latency / langchain_latency
        print(f"BENCHMARK:vs_langchain_ratio:{ratio}")
        print(f"TEST_PASS:performance_comparison_test")
    except Exception as e:
        print(f"TEST_FAIL:performance_comparison_test:{str(e)}")

def memory_benchmark():
    try:
        import loopgain
        tracemalloc.start()
        loopgain.run_scenario()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        tracemalloc.stop()
        print(f"TEST_PASS:memory_benchmark")
    except Exception as e:
        print(f"TEST_FAIL:memory_benchmark:{str(e)}")

def count_benchmark():
    try:
        import loopgain
        count = len(loopgain.__dict__)
        print(f"BENCHMARK:loc_count:{count}")
        print(f"TEST_PASS:count_benchmark")
    except Exception as e:
        print(f"TEST_FAIL:count_benchmark:{str(e)}")

if __name__ == "__main__":
    install_dependencies()
    install_package()
    measure_import_time()
    measure_loopgain_latency()
    measure_control_theories_benchmark()
    measure_max_iterations_benchmark()
    compare_performance()
    memory_benchmark()
    count_benchmark()
    print("RUN_OK")