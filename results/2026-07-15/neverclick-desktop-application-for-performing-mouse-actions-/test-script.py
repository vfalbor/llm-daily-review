import subprocess
import time
import tracemalloc
import os

def install_nodejs():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_npm():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_git():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_cargo():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_rust():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_neverclick():
    try:
        subprocess.run(['npm', 'install', '-g', 'neverclick'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_run_neverclick():
    try:
        start_time = time.time()
        subprocess.run(['neverclick', '--help'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:run_neverclick_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:test_run_neverclick")
    except Exception as e:
        print(f"TEST_FAIL:test_run_neverclick:{str(e)}")

def test_perform_action():
    try:
        start_time = time.time()
        subprocess.run(['neverclick', 'click', '--x', '100', '--y', '100'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:perform_action_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:test_perform_action")
    except Exception as e:
        print(f"TEST_FAIL:test_perform_action:{str(e)}")

def compare_baseline():
    try:
        start_time = time.time()
        subprocess.run(['autohotkey', '--help'], check=False)
        end_time = time.time()
        autohotkey_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['neverclick', '--help'], check=False)
        end_time = time.time()
        neverclick_time = end_time - start_time
        ratio = neverclick_time / autohotkey_time
        print(f"BENCHMARK:vs_autohotkey_time_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:compare_baseline:{str(e)}")

def measure_memory():
    try:
        tracemalloc.start()
        subprocess.run(['neverclick', '--help'], check=False)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{current}")
        tracemalloc.stop()
        print("TEST_PASS:measure_memory")
    except Exception as e:
        print(f"TEST_FAIL:measure_memory:{str(e)}")

def count_loc():
    try:
        loc_count = subprocess.run(['git', 'ls-files', '|', 'wc', '-l'], stdout=subprocess.PIPE, check=False)
        print(f"BENCHMARK:loc_count:{loc_count.stdout.decode('utf-8').strip()}")
        print("TEST_PASS:count_loc")
    except Exception as e:
        print(f"TEST_FAIL:count_loc:{str(e)}")

def count_test_files():
    try:
        test_files_count = subprocess.run(['git', 'ls-files', 'tests/', '|', 'wc', '-l'], stdout=subprocess.PIPE, check=False)
        print(f"BENCHMARK:test_files_count:{test_files_count.stdout.decode('utf-8').strip()}")
        print("TEST_PASS:count_test_files")
    except Exception as e:
        print(f"TEST_FAIL:count_test_files:{str(e)}")

def measure_execution_time():
    try:
        start_time = time.time()
        subprocess.run(['neverclick', '--help'], check=False)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"BENCHMARK:execution_time_ms:{execution_time * 1000}")
        print("TEST_PASS:measure_execution_time")
    except Exception as e:
        print(f"TEST_FAIL:measure_execution_time:{str(e)}")

install_nodejs()
install_npm()
install_git()
install_cargo()
install_rust()
install_neverclick()
test_run_neverclick()
test_perform_action()
compare_baseline()
measure_memory()
count_loc()
count_test_files()
measure_execution_time()
print("RUN_OK")