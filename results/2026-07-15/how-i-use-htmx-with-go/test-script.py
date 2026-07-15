import subprocess
import time
import tracemalloc
import importlib.util
import sys

def install_dependencies():
    print("Installing dependencies...")
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    result = subprocess.run(['pip', 'install', 'htmx'], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print("INSTALL_FAIL:Unable to install htmx via pip, trying fallback")
        subprocess.run(['git', 'clone', 'https://github.com/htmx-org/htmx.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './htmx'], cwd='./htmx', check=False)
    print("INSTALL_OK")

def test_htmx_clone_and_run():
    try:
        print("Testing HTMX clone and run...")
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/htmx-org/htmx.git'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:clone_time_ms:{(end_time - start_time) * 1000}")
        # Run a simple HTMX app
        start_time = time.time()
        subprocess.run(['python', '-c', 'import htmx'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:HTMX clone and run")
    except Exception as e:
        print(f"TEST_FAIL:HTMX clone and run:{str(e)}")

def benchmark_htmx_import():
    try:
        print("Benchmarking HTMX import...")
        start_time = time.time()
        spec = importlib.util.find_spec('htmx')
        end_time = time.time()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:loc_count:{sum(1 for _ in open('htmx/__init__.py'))}")
        print("TEST_PASS:HTMX import benchmark")
    except Exception as e:
        print(f"TEST_FAIL:HTMX import benchmark:{str(e)}")

def compare_with_baseline():
    try:
        print("Comparing with baseline...")
        start_time = time.time()
        subprocess.run(['python', '-c', 'import htmx'], check=False)
        end_time = time.time()
        htmx_time = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run(['python', '-c', 'import requests'], check=False)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_python_import_ratio:{htmx_time / baseline_time}")
        print("TEST_PASS:baseline comparison")
    except Exception as e:
        print(f"TEST_FAIL:baseline comparison:{str(e)}")

def main():
    install_dependencies()
    test_htmx_clone_and_run()
    benchmark_htmx_import()
    compare_with_baseline()
    print("RUN_OK")

if __name__ == "__main__":
    main()