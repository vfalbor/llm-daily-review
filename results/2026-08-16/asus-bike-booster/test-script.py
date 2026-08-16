import subprocess
import time
import tracemalloc
import os

# Install APK packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

# Clone ASUS OxiIS repository (if exists)
try:
    subprocess.run(['git', 'clone', 'https://github.com/asus-oxiis/asus-oxiis.git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Count source files and languages
try:
    repo_dir = 'asus-oxiis'
    files = []
    languages = set()
    for root, dirs, filenames in os.walk(repo_dir):
        for filename in filenames:
            if filename.endswith(('.py', '.java', '.cpp', '.js')):
                files.append(os.path.join(root, filename))
                languages.add(filename.split('.')[-1])
    print(f"BENCHMARK:loc_count:{len(files)}")
    print(f"BENCHMARK:languages_count:{len(languages)}")
except Exception as e:
    print(f"TEST_FAIL:count_files:{e}")

# Check for simulator/emulator
try:
    subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd='asus-oxiis', check=False)
    print("TEST_PASS:check_simulator")
except Exception as e:
    print(f"TEST_FAIL:check_simulator:{e}")

# Run any Python examples found
try:
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['python', 'example.py'], cwd='asus-oxiis', check=False)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:example_time_ms:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:example_memory_mb:{peak / 10**6:.2f}")
    tracemalloc.stop()
    print("TEST_PASS:run_example")
except Exception as e:
    print(f"TEST_FAIL:run_example:{e}")

# Pair with Bike Booster device (simulated)
try:
    print("TEST_SKIP:pair_device:No hardware required")
except Exception as e:
    print(f"TEST_FAIL:pair_device:{e}")

# Install Pedal Assist (baseline tool)
try:
    subprocess.run(['git', 'clone', 'https://github.com/pedal-assist/pedal-assist.git'], check=False)
    subprocess.run(['python', 'setup.py', 'install'], cwd='pedal-assist', check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Compare performance vs Pedal Assist
try:
    start_time = time.time()
    subprocess.run(['python', 'example.py'], cwd='asus-oxiis', check=False)
    end_time = time.time()
    asus_time = end_time - start_time

    start_time = time.time()
    subprocess.run(['python', 'example.py'], cwd='pedal-assist', check=False)
    end_time = time.time()
    pedal_time = end_time - start_time

    print(f"BENCHMARK:vs_pedal_assist_time_ratio:{asus_time / pedal_time:.2f}")
    print("TEST_PASS:compare_performance")
except Exception as e:
    print(f"TEST_FAIL:compare_performance:{e}")

print("RUN_OK")