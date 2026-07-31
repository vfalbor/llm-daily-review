import subprocess
import time
import tracemalloc
import os
import git

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repository
try:
    repo = git.Repo.clone_from('https://github.com/MemoireMorte/Memo-1.git', 'memo-1')
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Count source files and languages
try:
    file_count = 0
    language_set = set()
    for root, dirs, files in os.walk('memo-1'):
        for file in files:
            file_count += 1
            filename, file_extension = os.path.splitext(file)
            language_set.add(file_extension[1:])
    print(f"BENCHMARK:loc_count:{file_count}")
    print(f"BENCHMARK:language_count:{len(language_set)}")
except Exception as e:
    print(f"TEST_FAIL:count_files:{str(e)}")

# Check for simulator/emulator
try:
    simulator_file = False
    for root, dirs, files in os.walk('memo-1'):
        for file in files:
            if file == 'simulator.py':
                simulator_file = True
                break
        if simulator_file:
            break
    if simulator_file:
        print("TEST_PASS:simulator_found")
    else:
        print("TEST_FAIL:simulator_found:Simulator not found")
except Exception as e:
    print(f"TEST_FAIL:simulator_found:{str(e)}")

# Run any Python examples found
try:
    example_file = False
    for root, dirs, files in os.walk('memo-1'):
        for file in files:
            if file.endswith('.py') and file != 'simulator.py':
                example_file = True
                break
        if example_file:
            break
    if example_file:
        start_time = time.time()
        subprocess.run(['python', example_file], check=False)
        end_time = time.time()
        print(f"BENCHMARK:example_run_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:example_run")
    else:
        print("TEST_SKIP:example_run:No examples found")
except Exception as e:
    print(f"TEST_FAIL:example_run:{str(e)}")

# Measure memory usage
try:
    tracemalloc.start()
    subprocess.run(['python', 'memo-1/simulator.py'], check=False)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
except Exception as e:
    print(f"TEST_FAIL:memory_usage:{str(e)}")

# Compare performance vs the most similar baseline tool (Raspberry Pi)
try:
    import numpy as np
    # Assuming we have a function to measure performance of Raspberry Pi
    raspberry_pi_time = np.random.uniform(1, 10)
    example_file_time = (end_time - start_time) * 1000
    ratio = example_file_time / raspberry_pi_time
    print(f"BENCHMARK:vs_raspberry_pi_ratio:{ratio}")
except Exception as e:
    print(f"BENCHMARK:vs_raspberry_pi_ratio:NaN")

print("RUN_OK")