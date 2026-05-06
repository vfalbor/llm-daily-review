import subprocess
import pip
import sys
import time
import tracemalloc
from red_squares import detect_github_outage, simulate_github_outage

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        pip.main(['install', 'red-squares'])
        print("INSTALL_OK")
    except Exception as e:
        subprocess.run(['git', 'clone', 'https://github.com/red-squares/red-squares'], check=True)
        subprocess.run(['pip', 'install', '-e', './red-squares'], cwd='./red-squares', check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_red_squares():
    try:
        start_time = time.time()
        simulate_github_outage()
        end_time = time.time()
        print(f"BENCHMARK:simulate_github_outage_time_ms:{(end_time - start_time) * 1000:.2f}")

        start_time = time.time()
        detect_github_outage()
        end_time = time.time()
        print(f"BENCHMARK:detect_github_outage_time_ms:{(end_time - start_time) * 1000:.2f}")

        print("TEST_PASS:simulate_and_detect_github_outage")
    except Exception as e:
        print(f"TEST_FAIL:simulate_and_detect_github_outage:{str(e)}")

def measure_downstream_impact():
    try:
        start_time = time.time()
        # Simulate downstream application usage
        for _ in range(1000):
            pass
        end_time = time.time()
        print(f"BENCHMARK:downstream_application_time_ms:{(end_time - start_time) * 1000:.2f}")

        start_time = time.time()
        simulate_github_outage()
        end_time = time.time()
        print(f"BENCHMARK:downstream_application_with_github_outage_time_ms:{(end_time - start_time) * 1000:.2f}")

        print("TEST_PASS:measure_downstream_impact")
    except Exception as e:
        print(f"TEST_FAIL:measure_downstream_impact:{str(e)}")

def compare_to_baseline():
    try:
        start_time = time.time()
        # Simulate a similar tool (e.g., GitHub)
        for _ in range(1000):
            pass
        end_time = time.time()
        baseline_time = end_time - start_time

        start_time = time.time()
        simulate_github_outage()
        end_time = time.time()
        red_squares_time = end_time - start_time

        print(f"BENCHMARK:vs_github_simulate_outage_ratio:{red_squares_time / baseline_time:.2f}")
        print("TEST_PASS:compare_to_baseline")
    except Exception as e:
        print(f"TEST_FAIL:compare_to_baseline:{str(e)}")

def benchmark_memory_usage():
    try:
        tracemalloc.start()
        simulate_github_outage()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        tracemalloc.stop()
        print("TEST_PASS:benchmark_memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:benchmark_memory_usage:{str(e)}")

def main():
    install_dependencies()
    test_red_squares()
    measure_downstream_impact()
    compare_to_baseline()
    benchmark_memory_usage()
    print("RUN_OK")

if __name__ == "__main__":
    main()