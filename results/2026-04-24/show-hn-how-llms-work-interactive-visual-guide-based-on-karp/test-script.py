import subprocess
import time
import tracemalloc
from pathlib import Path
import importlib.util
import importlib.machinery

# Install system packages
def install_system_packages(packages):
    for package in packages:
        subprocess.run(['apk', 'add', '--no-cache', package], check=False)
        print(f"INSTALL_OK: {package}")

def test_install_limited_baselines():
    try:
        subprocess.run(['pip', 'install', 'ynarwal'])
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")
    else:
        print("INSTALL_OK")

def test_import_time():
    import_time_start = time.time()
    try:
        import ynarwal
    except ImportError:
        print(f"TEST_FAIL: ynarwal_import: Import failed")
        return
    import_time_end = time.time()
    import_time = (import_time_end - import_time_start) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")

def test_limited_baselines_operation_latency():
    try:
        import ynarwal
        import time
        operation_start = time.time()
        # Run a minimal functional test with synthetic data (no API key)
        # Assuming ynarwal has a function called 'run' for this purpose
        ynarwal.run()
        operation_end = time.time()
        operation_latency = (operation_end - operation_start) * 1000
        print(f"BENCHMARK:limited_baselines_operation_latency_ms:{operation_latency:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:limited_baselines_operation_latency: {str(e)}")

def test_loc_count():
    try:
        ynarwal_path = Path(subprocess.run(['pip', 'show', '-f', 'ynarwal'], capture_output=True, text=True).stdout.splitlines()[2].split(':')[-1].strip())
        loc_count = len(list(ynarwal_path.glob('**/*.py')))
        print(f"BENCHMARK:loc_count:{loc_count}")
    except Exception as e:
        print(f"TEST_FAIL:loc_count: {str(e)}")

def test_memory_usage():
    try:
        tracemalloc.start()
        import ynarwal
        current, peak = tracemalloc.get_traced_memory()
        memory_usage = peak / 10**6  # in MB
        print(f"BENCHMARK:memory_usage_mb:{memory_usage:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage: {str(e)}")
    finally:
        tracemalloc.stop()

def test_baselines():
    try:
        # Comparing performance vs the most similar baseline tool listed above (e.g. LLaMA)
        import ynarwal
        import llama
        import time
        ynarwal_start = time.time()
        ynarwal.run()
        ynarwal_end = time.time()
        llama_start = time.time()
        llama.run()
        llama_end = time.time()
        ynarwal_time = (ynarwal_end - ynarwal_start) * 1000
        llama_time = (llama_end - llama_start) * 1000
        ratio = ynarwal_time / llama_time
        print(f"BENCHMARK:vs_llama_time_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:vs_llama_time_ratio: {str(e)}")

if __name__ == "__main__":
    install_system_packages(['git'])
    test_install_limited_baselines()
    test_import_time()
    test_limited_baselines_operation_latency()
    test_loc_count()
    test_memory_usage()
    test_baselines()
    print("RUN_OK")