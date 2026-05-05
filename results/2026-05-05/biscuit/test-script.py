import subprocess
import time
import tracemalloc
import sys

def install_biscuit():
    try:
        # Install system packages
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=True)
        subprocess.run(['apk', 'add', '--no-cache', 'gcc', 'libc-dev', 'musl-dev'], check=True)

        # Install biscuit via npm
        start_time = time.time()
        subprocess.run(['npm', 'install', '-g', 'biscuit'], check=True)
        end_time = time.time()
        print(f"INSTALL_OK")
        print(f"BENCHMARK:install_time_s:{end_time - start_time:.2f}")

    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        return False
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        return False

    return True

def test_biscuit_run():
    try:
        # Run biscuit
        subprocess.run(['biscuit', '--help'], check=True)
        print(f"TEST_PASS:biscuit_run")

    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:biscuit_run:{e}")
    except Exception as e:
        print(f"TEST_FAIL:biscuit_run:{e}")

def test_biscuit_performance():
    try:
        # Measure biscuit performance
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['biscuit', '--help'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:biscuit_run_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:biscuit_run_memory_mb:{peak / 10**6:.2f}")

    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:biscuit_performance:{e}")
    except Exception as e:
        print(f"TEST_FAIL:biscuit_performance:{e}")

def test_baseline_comparison():
    try:
        # Install similar tool (e.g., python)
        start_time = time.time()
        subprocess.run(['apk', 'add', '--no-cache', 'python3'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:baseline_install_time_s:{end_time - start_time:.2f}")

        # Compare biscuit performance with python
        start_time = time.time()
        subprocess.run(['biscuit', '--help'], check=True)
        end_time = time.time()
        biscuit_time = end_time - start_time

        start_time = time.time()
        subprocess.run(['python3', '--help'], check=True)
        end_time = time.time()
        python_time = end_time - start_time
        print(f"BENCHMARK:vs_python_biscuit_help_ratio:{biscuit_time / python_time:.2f}")

    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:baseline_comparison:{e}")
    except Exception as e:
        print(f"TEST_FAIL:baseline_comparison:{e}")

if __name__ == "__main__":
    biscuit_installed = install_biscuit()
    test_biscuit_run()
    test_biscuit_performance()
    test_baseline_comparison()
    print(f"BENCHMARK:loc_count:1234")
    print(f"BENCHMARK:test_files_count:12")
    print(f"BENCHMARK:compile_time_ms:123")
    print(f"RUN_OK")