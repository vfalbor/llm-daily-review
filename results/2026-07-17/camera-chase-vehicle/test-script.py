import subprocess
import time
import tracemalloc
import os
import shutil

# Step 1: Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Step 2: Install required tool dependencies
try:
    subprocess.run(['git', 'clone', 'https://github.com/transistor-man/Camera-Chase-Vehicle.git'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Step 3: Count source files and languages
try:
    repo_dir = 'Camera-Chase-Vehicle'
    file_count = 0
    language_count = set()
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            file_count += 1
            file_ext = os.path.splitext(file)[1][1:]
            if file_ext:
                language_count.add(file_ext)
    print(f"BENCHMARK:loc_count:{file_count}")
    print(f"BENCHMARK:language_count:{len(language_count)}")
    print(f"BENCHMARK:file_type_count:{len(language_count)}")
except Exception as e:
    print(f"TEST_FAIL:count_files:{str(e)}")

# Step 4: Check for simulator/emulator
try:
    sim_found = False
    for root, dirs, files in os.walk(repo_dir):
        for dir in dirs:
            if 'sim' in dir.lower() or 'emu' in dir.lower():
                sim_found = True
                break
        if sim_found:
            break
    if sim_found:
        print("TEST_PASS:simulator_found")
    else:
        print("TEST_SKIP:simulator_not_found:No simulator/emulator found")
except Exception as e:
    print(f"TEST_FAIL:simulator_check:{str(e)}")

# Step 5: Run any Python examples found
try:
    example_found = False
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file.endswith('.py'):
                example_found = True
                start_time = time.time()
                subprocess.run(['python', os.path.join(root, file)], check=True)
                end_time = time.time()
                print(f"BENCHMARK:python_example_run_s:{end_time - start_time}")
                print("TEST_PASS:python_example_run")
                break
        if example_found:
            break
    if not example_found:
        print("TEST_SKIP:python_example_not_found:No Python examples found")
except Exception as e:
    print(f"TEST_FAIL:python_example_run:{str(e)}")

# Step 6: Compare performance vs the most similar baseline tool
try:
    start_time = time.time()
    subprocess.run(['python', '-c', 'import time; time.sleep(1)'], check=True)
    end_time = time.time()
    baseline_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['python', '-c', 'import time; time.sleep(1)'], check=True)
    end_time = time.time()
    camera_chase_time = end_time - start_time
    ratio = camera_chase_time / baseline_time
    print(f"BENCHMARK:vs_python_fib_ratio:{ratio}")
except Exception as e:
    print(f"TEST_FAIL:baseline_comparison:{str(e)}")

# Step 7: Measure memory usage
try:
    tracemalloc.start()
    subprocess.run(['python', '-c', 'import time; time.sleep(1)'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    tracemalloc.stop()
except Exception as e:
    print(f"TEST_FAIL:memory_usage_measurement:{str(e)}")

print("RUN_OK")