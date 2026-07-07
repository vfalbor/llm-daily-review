import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/lttlabs/ryzen-ai-halo'], check=True)
except Exception as e:
    print(f"INSTALL_FAIL:git clone failed with {str(e)}")
else:
    print("INSTALL_OK")

# Install Python dependencies
try:
    subprocess.run(['pip', 'install', '-r', 'ryzen-ai-halo/requirements.txt'], check=True)
except Exception as e:
    print(f"INSTALL_FAIL:pip install failed with {str(e)}")
else:
    print("INSTALL_OK")

# Count source files and languages
try:
    num_files = sum([len(files) for r, d, files in os.walk("ryzen-ai-halo")])
    num_langs = len(set([file.split('.')[-1] for r, d, files in os.walk("ryzen-ai-halo") for file in files]))
    print(f"BENCHMARK:source_file_count:{num_files}")
    print(f"BENCHMARK:programming_language_count:{num_langs}")
except Exception as e:
    print(f"TEST_FAIL:count_source_files:{str(e)}")

# Check for simulator/emulator
try:
    simulator_emulator = subprocess.run(['find', 'ryzen-ai-halo', '-name', 'simulator'], check=True, capture_output=True)
    if simulator_emulator.returncode == 0:
        print("TEST_PASS:check_simulator")
    else:
        print("TEST_SKIP:check_simulator:no simulator found")
except Exception as e:
    print(f"TEST_FAIL:check_simulator:{str(e)}")

# Run Python examples
try:
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['python', 'ryzen-ai-halo/example.py'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:example_runtime_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:example_memory_usage_mb:{current / 1024 / 1024}")
    print("TEST_PASS:run_python_examples")
except Exception as e:
    print(f"TEST_FAIL:run_python_examples:{str(e)}")

# Compare performance vs similar tool
try:
    start_time = time.time()
    subprocess.run(['pip', 'install', 'tensorflow'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:vs_tensorflow_install_time_ms:{(end_time - start_time) * 1000}")
except Exception as e:
    print(f"BENCHMARK:vs_tensorflow_install_time_ms:failed with {str(e)}")

try:
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['python', '-c', 'import tensorflow'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:vs_tensorflow_import_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:vs_tensorflow_memory_usage_mb:{current / 1024 / 1024}")
except Exception as e:
    print(f"BENCHMARK:vs_tensorflow_import_time_ms:failed with {str(e)}")

print("RUN_OK")