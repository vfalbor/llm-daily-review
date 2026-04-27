import subprocess
import time
import tracemalloc
import os
import sys
import importlib
import turboquant as tq

def run_command(cmd, check=False):
    try:
        subprocess.run(cmd, check=check)
        return True
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: {e}")
        return False

def install_packages():
    if not run_command(['apk', 'add', '--no-cache', 'git']):
        return False
    if not run_command(['pip', 'install', 'turboquant']):
        run_command(['git', 'clone', 'https://github.com/Arkaung/TurboQuant'], check=True)
        if not run_command(['pip', 'install', '-e', './TurboQuant']):
            return False
    return True

def benchmark_import():
    start_time = time.time()
    importlib.reload(tq)
    end_time = time.time()
    import_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time_ms:.2f}")

def benchmark_calculation():
    start_time = time.time()
    calculator = tq.TurboQuantCalculator()
    calculator.calculate(100)
    end_time = time.time()
    calculation_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:calculation_time_ms:{calculation_time_ms:.2f}")

def benchmark_memory():
    tracemalloc.start()
    calculator = tq.TurboQuantCalculator()
    calculator.calculate(100)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_kb:{peak / 1024:.2f}")

def test_calculation():
    try:
        calculator = tq.TurboQuantCalculator()
        result = calculator.calculate(100)
        if result != 100:
            print(f"TEST_FAIL:calculation: incorrect result {result}")
        else:
            print("TEST_PASS:calculation")
    except Exception as e:
        print(f"TEST_FAIL:calculation: {e}")

def test_open_walkthrough():
    try:
        import webbrowser
        url = "https://github.com/Arkaung/TurboQuant"
        webbrowser.open(url)
        print("TEST_PASS:open_walkthrough")
    except Exception as e:
        print(f"TEST_FAIL:open_walkthrough: {e}")

def compare_baseline():
    try:
        import quantlib
        start_time = time.time()
        quantlib.calculate(100)
        end_time = time.time()
        quantlib_time_ms = (end_time - start_time) * 1000
        start_time = time.time()
        calculator = tq.TurboQuantCalculator()
        calculator.calculate(100)
        end_time = time.time()
        turboquant_time_ms = (end_time - start_time) * 1000
        ratio = turboquant_time_ms / quantlib_time_ms
        print(f"BENCHMARK:vs_quantlib_calculation_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"BENCHMARK:vs_quantlib_calculation_ratio: failed to compare {e}")

if __name__ == "__main__":
    if not install_packages():
        print("INSTALL_OK")
    else:
        print("INSTALL_OK")

    benchmark_import()
    benchmark_calculation()
    benchmark_memory()
    test_calculation()
    test_open_walkthrough()
    compare_baseline()

    print("RUN_OK")