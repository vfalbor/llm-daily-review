import subprocess
import time
import tracemalloc
import requests

def get_benchmark(name, setup, func):
    tracemalloc.start()
    start_time = time.time()
    func()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:{name}_time_s:{end_time - start_time}")
    print(f"BENCHMARK:{name}_memory_mb:{peak / 1024 / 1024}")

def test_install():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        subprocess.run(['npm', 'install'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_lbse_rendering():
    try:
        # Send HTTP request to test rendering performance
        start_time = time.time()
        response = requests.get('http://localhost:8080', timeout=5)
        end_time = time.time()
        print(f"TEST_PASS:lbse_rendering")
        print(f"BENCHMARK:lbse_rendering_time_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:lbse_rendering:{str(e)}")

def test_edge_cases():
    try:
        # Send HTTP request to test edge cases
        start_time = time.time()
        response = requests.get('http://localhost:8080/edge_case', timeout=5)
        end_time = time.time()
        print(f"TEST_PASS:edge_cases")
        print(f"BENCHMARK:edge_cases_time_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:edge_cases:{str(e)}")

def compare_with_baseline():
    try:
        # Send HTTP request to test baseline performance
        start_time = time.time()
        response = requests.get('http://localhost:8081', timeout=5)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        lbse_time = float(next(line.split(":")[1] for line in open('benchmark.log') if 'lbse_rendering_time_ms' in line))
        ratio = lbse_time / baseline_time
        print(f"BENCHMARK:vs_python_lbs_rendering_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_baseline:{str(e)}")

def main():
    test_install()
    # Start server in background
    subprocess.Popen(['node', 'server.js'])
    time.sleep(1)  # wait for server to start
    test_lbse_rendering()
    test_edge_cases()
    compare_with_baseline()
    print("RUN_OK")

if __name__ == "__main__":
    main()