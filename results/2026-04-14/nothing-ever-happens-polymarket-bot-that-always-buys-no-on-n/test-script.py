import subprocess
import time
import tracemalloc
import importlib.util
import random
import sys

def install_packages():
    print("INSTALLING DEPENDENCIES...")
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    try:
        subprocess.run(['pip', 'install', 'nothing-ever-happens'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        subprocess.run(['git', 'clone', 'https://github.com/sterlingcrispin/nothing-ever-happens.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './nothing-ever-happens'], cwd='./nothing-ever-happens', check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def test_import():
    try:
        spec = importlib.util.find_spec('nothing_ever_happens')
        if spec is None:
            raise ImportError
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tracemalloc.start()
        start_time = time.time()
        import nothing_ever_happens
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:import_memory_mb:{peak / 10**6:.2f}")
        print("TEST_PASS:import")
    except Exception as e:
        print(f"TEST_FAIL:import:{e}")

def test_bot():
    try:
        import nothing_ever_happens
        tracemalloc.start()
        start_time = time.time()
        # Mock API call with a fake key
        nothing_ever_happens.buy_no("fake_key", "test_market")
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:buy_no_latency_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:buy_no_memory_mb:{peak / 10**6:.2f}")
        print("TEST_PASS:buy_no")
    except Exception as e:
        print(f"TEST_FAIL:buy_no:{e}")

def test_reliability():
    try:
        import nothing_ever_happens
        tracemalloc.start()
        start_time = time.time()
        # Mock API call with a fake key
        for _ in range(10):
            nothing_ever_happens.buy_no("fake_key", "test_market")
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:reliability_latency_ms:{(end_time - start_time) * 1000 / 10:.2f}")
        print(f"BENCHMARK:reliability_memory_mb:{peak / 10**6:.2f}")
        print("TEST_PASS:reliability")
    except Exception as e:
        print(f"TEST_FAIL:reliability:{e}")

def test_stability():
    try:
        import nothing_ever_happens
        tracemalloc.start()
        start_time = time.time()
        # Mock API call with a fake key
        for _ in range(100):
            nothing_ever_happens.buy_no("fake_key", "test_market")
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:stability_latency_ms:{(end_time - start_time) * 1000 / 100:.2f}")
        print(f"BENCHMARK:stability_memory_mb:{peak / 10**6:.2f}")
        print("TEST_PASS:stability")
    except Exception as e:
        print(f"TEST_FAIL:stability:{e}")

def compare_baseline():
    try:
        import nothing_ever_happens
        import random
        tracemalloc.start()
        start_time = time.time()
        nothing_ever_happens.buy_no("fake_key", "test_market")
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        baseline_time = time.time()
        # Mock a random buyer
        for _ in range(10):
            if random.random() < 0.5:
                pass
        baseline_end_time = time.time()
        print(f"BENCHMARK:vs_random_buyer_ratio:{(end_time - start_time) / (baseline_end_time - baseline_time):.2f}")
        print("TEST_PASS:compare_baseline")
    except Exception as e:
        print(f"TEST_FAIL:compare_baseline:{e}")

install_packages()
test_import()
test_bot()
test_reliability()
test_stability()
compare_baseline()
print("RUN_OK")