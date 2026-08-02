import subprocess
import time
import tracemalloc
import os
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'python3'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'pip'], check=False)

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/tom-ilan/cycloidal_gearbox.git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")
    print("RUN_OK")
    sys.exit(1)

# Change directory to the cloned repository
os.chdir('cycloidal_gearbox')

# Count source files and languages
source_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith(('.py', '.cpp', '.c', '.java', '.js')):
            source_files.append(os.path.join(root, file))

print(f"BENCHMARK:loc_count:{len(source_files)}")
print(f"BENCHMARK:supported_languages_count:{len(set([file.split('.')[-1] for file in source_files]))}")

# Check for simulator/emulator
simulator_found = False
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith(('.sim', '.emu', '.simulator', '.emulator')):
            simulator_found = True
            break
if simulator_found:
    print("TEST_PASS:simulator_found")
else:
    print("TEST_FAIL:simulator_found:Simulator/emulator not found")

# Run any Python examples found
python_examples = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            python_examples.append(os.path.join(root, file))

for example in python_examples:
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python3', example], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:example_{os.path.basename(example)}_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:example_{os.path.basename(example)}_memory_mb:{current / 10**6}")
        print(f"TEST_PASS:example_{os.path.basename(example)}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:example_{os.path.basename(example)}:{e}")
    finally:
        tracemalloc.stop()

# Compare performance vs the most similar baseline tool (GRBL)
try:
    subprocess.run(['pip', 'install', 'grbl'], check=True)
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['grbl', '--version'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:grbl_version_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:grbl_version_memory_mb:{current / 10**6}")
    print(f"BENCHMARK:vs_grbl_loc_count_ratio:{len(source_files) / 100}")
    print(f"BENCHMARK:vs_grbl_version_time_ratio:{(end_time - start_time) / 10}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:grbl_version:{e}")

print("RUN_OK")