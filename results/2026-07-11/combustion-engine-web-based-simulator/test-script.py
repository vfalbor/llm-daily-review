import subprocess
import time
import tracemalloc
import os

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/combustion-lab/web_simulator.git'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print("INSTALL_FAIL:git clone failed with", str(e))

# Change directory to the cloned repository
os.chdir('web_simulator')

# Count source files and languages
try:
    source_files = subprocess.run(['find', '.', '-type', 'f'], capture_output=True, text=True).stdout.splitlines()
    source_file_count = len(source_files)
    languages = set()
    for file in source_files:
        if file.endswith('.py'):
            languages.add('Python')
        elif file.endswith('.js'):
            languages.add('JavaScript')
        elif file.endswith('.html'):
            languages.add('HTML')
    print("BENCHMARK:loc_count:", source_file_count)
    print("BENCHMARK:languages_count:", len(languages))
except Exception as e:
    print("TEST_FAIL:count source files and languages:", str(e))

# Try to run Python examples
try:
    python_files = [file for file in source_files if file.endswith('.py')]
    for file in python_files:
        subprocess.run(['python', file], check=True)
    print("TEST_PASS:run Python examples")
except Exception as e:
    print("TEST_FAIL:run Python examples:", str(e))

# Benchmark performance
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['python', '-c', 'import web_simulator'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print("BENCHMARK:import_time_ms:", (end_time - start_time) * 1000)
    print("BENCHMARK:import_memory_mb:", current / 1024 / 1024)
    tracemalloc.stop()
    print("TEST_PASS:benchmark performance")
except Exception as e:
    print("TEST_FAIL:benchmark performance:", str(e))

# Try to interact with the simulator
try:
    subprocess.run(['python', '-c', 'import web_simulator; web_simulator.interact()'], check=True)
    print("TEST_PASS:interact with the simulator")
except Exception as e:
    print("TEST_FAIL:interact with the simulator:", str(e))

# Compare performance with baseline tool (assuming it's a Python package)
try:
    start_time = time.time()
    subprocess.run(['python', '-c', 'import baseline_tool'], check=True)
    end_time = time.time()
    baseline_time = end_time - start_time
    print("BENCHMARK:vs_baseline_import_time_ms:", baseline_time * 1000)
    print("BENCHMARK:vs_baseline_import_time_ratio:", (end_time - start_time) / baseline_time)
    print("TEST_PASS:compare performance with baseline tool")
except Exception as e:
    print("TEST_FAIL:compare performance with baseline tool:", str(e))

print("RUN_OK")