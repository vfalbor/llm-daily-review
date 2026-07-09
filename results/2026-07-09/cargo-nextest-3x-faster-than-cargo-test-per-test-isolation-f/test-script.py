import subprocess
import sys
import time
import tracemalloc
import importlib.util

def install_nextest():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', 'nextest'], check=False)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/nextest-rs/nextest.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './nextest'], check=False)
            print("INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:{e}")

def run_test_nextest():
    try:
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['nextest', 'run'], check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:nextest_run_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:nextest_run_memory_mb:{current / (1024 * 1024)}")
        print(f"TEST_PASS:nextest_run")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:nextest_run:{e}")
    except Exception as e:
        print(f"TEST_FAIL:nextest_run:{e}")

def run_test_cargo_benchmark():
    try:
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['cargo', 'benchmark'], check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:cargo_benchmark_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:cargo_benchmark_memory_mb:{current / (1024 * 1024)}")
        print(f"TEST_PASS:cargo_benchmark")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:cargo_benchmark:{e}")
    except Exception as e:
        print(f"TEST_FAIL:cargo_benchmark:{e}")

def compare_benchmark():
    try:
        nextest_time = float(next((line.split(":")[1] for line in sys.stdout.getvalue().decode().splitlines() if "nextest_run_time_ms" in line), None))
        cargo_time = float(next((line.split(":")[1] for line in sys.stdout.getvalue().decode().splitlines() if "cargo_benchmark_time_ms" in line), None))
        print(f"BENCHMARK:vs_cargo_benchmark_time_ratio:{nextest_time / cargo_time}")
    except Exception as e:
        print(f"BENCHMARK:vs_cargo_benchmark_time_ratio:unknown")

def import_nextest():
    try:
        start_time = time.time()
        spec = importlib.util.find_spec("nextest")
        end_time = time.time()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:import_nextest")
    except Exception as e:
        print(f"TEST_FAIL:import_nextest:{e}")

def main():
    install_nextest()
    import_nextest()
    run_test_nextest()
    run_test_cargo_benchmark()
    compare_benchmark()
    print("RUN_OK")

if __name__ == "__main__":
    import nextest
    main()