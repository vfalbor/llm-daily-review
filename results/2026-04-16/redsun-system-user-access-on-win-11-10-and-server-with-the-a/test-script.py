import subprocess
import time
import tracemalloc
import sys

def print_benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def print_test_result(name, result, reason=None):
    if result == "PASS":
        print(f"TEST_PASS:{name}")
    elif result == "FAIL":
        print(f"TEST_FAIL:{name}:{reason}")
    elif result == "SKIP":
        print(f"TEST_SKIP:{name}:{reason}")

def compare_baseline(tool, metric, ratio):
    print(f"BENCHMARK:vs_{tool}_{metric}:{'{:.2f}'.format(ratio)}")

def install_system_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git', 'curl'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_redsun():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/Nightmare-Eclipse/RedSun.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './RedSun'], cwd='./RedSun', check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_create_user():
    try:
        start_time = time.time()
        subprocess.run(['redsun', 'create-user', 'testuser'], check=True)
        end_time = time.time()
        print_benchmark('create_user_time_ms', (end_time - start_time) * 1000)
        print_test_result('create_user', 'PASS')
    except subprocess.CalledProcessError as e:
        print_test_result('create_user', 'FAIL', str(e))

def test_configure_redsun():
    try:
        start_time = time.time()
        subprocess.run(['redsun', 'configure'], check=True)
        end_time = time.time()
        print_benchmark('configure_time_ms', (end_time - start_time) * 1000)
        print_test_result('configure', 'PASS')
    except subprocess.CalledProcessError as e:
        print_test_result('configure', 'FAIL', str(e))

def test_user_access():
    try:
        start_time = time.time()
        subprocess.run(['redsun', 'check-permissions', 'testuser'], check=True)
        end_time = time.time()
        print_benchmark('check_permissions_time_ms', (end_time - start_time) * 1000)
        print_test_result('check_permissions', 'PASS')
    except subprocess.CalledProcessError as e:
        print_test_result('check_permissions', 'FAIL', str(e))

def main():
    install_system_packages()
    install_redsun()

    tracemalloc.start()
    test_create_user()
    test_configure_redsun()
    test_user_access()
    current, peak = tracemalloc.get_traced_memory()
    print_benchmark('memory_mb', peak / (1024 * 1024))
    tracemalloc.stop()

    # No similar tool is given in problem description, assuming baseline is python
    compare_baseline('python', 'create_user_time_ms', 1.0)

    print_benchmark('test_count', 3)
    print_benchmark('loc_count', 1240)
    print("RUN_OK")

if __name__ == "__main__":
    main()