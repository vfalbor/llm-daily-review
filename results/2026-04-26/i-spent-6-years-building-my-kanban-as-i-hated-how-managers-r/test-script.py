import subprocess
import sys
import time
import tracemalloc
import importlib.util

def install_packages(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install {package}: {e}")
        sys.exit(1)

def install_tool(package):
    try:
        subprocess.run(['pip', 'install', package], check=True)
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/okayke/ooko.git'], check=True)
            subprocess.run(['pip', 'install', '-e', 'ooko'], check=True, cwd='ooko')
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:Failed to install {package}: {e}")
            sys.exit(1)

def test_install():
    try:
        start_time = time.time()
        install_packages('git')
        install_tool('ooko')
        end_time = time.time()
        print(f"BENCHMARK:install_time_s:{end_time - start_time:.2f}")
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:Failed to install: {e}")

def test_create_board():
    try:
        start_time = time.time()
        subprocess.run(['ooko', 'create', 'board'], check=True)
        subprocess.run(['ooko', 'add', 'column', 'board'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:create_board_time_s:{end_time - start_time:.2f}")
        print("TEST_PASS:create_board")
    except Exception as e:
        print(f"TEST_FAIL:create_board:{e}")

def test_performance():
    try:
        start_time = time.time()
        for i in range(100):
            subprocess.run(['ooko', 'create', 'board'], check=True)
            subprocess.run(['ooko', 'add', 'column', 'board'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:performance_time_s:{end_time - start_time:.2f}")
        print("TEST_PASS:performance")
    except Exception as e:
        print(f"TEST_FAIL:performance:{e}")

def test_import():
    try:
        start_time = time.time()
        subprocess.run(['ooko', 'import', 'trello'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:import_time_s:{end_time - start_time:.2f}")
        print("TEST_PASS:import")
    except Exception as e:
        print(f"TEST_FAIL:import:{e}")

def test_baseline():
    try:
        start_time = time.time()
        subprocess.run(['trello', 'create', 'board'], check=True)
        end_time = time.time()
        baseline_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['ooko', 'create', 'board'], check=True)
        end_time = time.time()
        ooko_time = end_time - start_time
        print(f"BENCHMARK:vs_trello_create_board_ratio:{ooko_time / baseline_time:.2f}")
        print("TEST_PASS:baseline")
    except Exception as e:
        print(f"TEST_FAIL:baseline:{e}")

def test_memory():
    try:
        tracemalloc.start()
        subprocess.run(['ooko', 'create', 'board'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        tracemalloc.stop()
        print("TEST_PASS:memory")
    except Exception as e:
        print(f"TEST_FAIL:memory:{e}")

def main():
    test_install()
    test_create_board()
    test_performance()
    test_import()
    test_baseline()
    test_memory()
    print("RUN_OK")

if __name__ == "__main__":
    main()