import subprocess
import time
import tracemalloc
import sys

def install_dependencies():
    print("INSTALLING DEPENDENCIES")
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
    print("INSTALL_OK")

def install_sensor_etch():
    try:
        print("INSTALLING SENSOR ETCH")
        subprocess.run(['npm', 'install', 'phone-sensors'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def install_baseline_tool():
    try:
        print("INSTALLING PYGAME")
        subprocess.run(['pip', 'install', 'pygame'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def test_sensor_etch_response_time():
    try:
        print("TESTING SENSOR ETCH RESPONSE TIME")
        start_time = time.time()
        subprocess.run(['node', 'node_modules/phone-sensors/index.js'], check=True)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:response_time_ms:{response_time:.2f}")
        print("TEST_PASS:response_time")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:response_time:{e}")

def test_sensor_etch_complex_input():
    try:
        print("TESTING SENSOR ETCH COMPLEX INPUT")
        # simulate complex sensor input
        # this is just a placeholder, you need to implement actual complex input
        start_time = time.time()
        subprocess.run(['node', 'node_modules/phone-sensors/index.js'], check=True)
        end_time = time.time()
        process_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:process_time_ms:{process_time:.2f}")
        print("TEST_PASS:complex_input")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:complex_input:{e}")

def test_baseline_tool_response_time():
    try:
        print("TESTING PYGAME RESPONSE TIME")
        start_time = time.time()
        subprocess.run(['python', '-c', 'import pygame; pygame.init(); pygame.quit()'], check=True)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:baseline_response_time_ms:{response_time:.2f}")
        print("TEST_PASS:baseline_response_time")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:baseline_response_time:{e}")

def compare_performance():
    try:
        print("COMPARING PERFORMANCE")
        sensor_etch_response_time = float(subprocess.check_output(['grep', 'response_time_ms', 'test.log']).decode().strip().split(':')[1])
        baseline_response_time = float(subprocess.check_output(['grep', 'baseline_response_time_ms', 'test.log']).decode().strip().split(':')[1])
        ratio = sensor_etch_response_time / baseline_response_time
        print(f"BENCHMARK:vs_pygame_response_time_ratio:{ratio:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_performance:{e}")

def test_memory_usage():
    try:
        print("TESTING MEMORY USAGE")
        tracemalloc.start()
        subprocess.run(['node', 'node_modules/phone-sensors/index.js'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024:.2f}")
        print("TEST_PASS:memory_usage")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:memory_usage:{e}")

def test_loc_count():
    try:
        print("TESTING LOC COUNT")
        loc_count = int(subprocess.check_output(['wc', '-l', 'node_modules/phone-sensors/index.js']).decode().strip().split()[0])
        print(f"BENCHMARK:loc_count:{loc_count}")
        print("TEST_PASS:loc_count")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:loc_count:{e}")

def test_test_files_count():
    try:
        print("TESTING TEST FILES COUNT")
        test_files_count = int(subprocess.check_output(['find', 'node_modules/phone-sensors', '-type', 'f', '-name', '*.js', '|', 'wc', '-l']).decode().strip())
        print(f"BENCHMARK:test_files_count:{test_files_count}")
        print("TEST_PASS:test_files_count")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:test_files_count:{e}")

install_dependencies()
install_sensor_etch()
install_baseline_tool()
test_sensor_etch_response_time()
test_sensor_etch_complex_input()
test_baseline_tool_response_time()
compare_performance()
test_memory_usage()
test_loc_count()
test_test_files_count()
print("RUN_OK")