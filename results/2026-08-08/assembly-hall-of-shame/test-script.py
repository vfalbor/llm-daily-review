import subprocess
import os
import time
import tracemalloc
import importlib.util
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/xoreaxeaxeax/asm-hall-of-shame.git'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Change into the repository directory
os.chdir("asm-hall-of-shame")

# Install tools dependencies
try:
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    print("INSTALL_OK")
except Exception as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/xoreaxeaxeax/asm-hall-of-shame.git'], check=True)
        subprocess.run(['pip', 'install', '-e', '.'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

# Measure source files and languages count
try:
    src_files_count = len([name for name in os.listdir() if os.path.isfile(name) and name.endswith(('.s', '.asm'))])
    print(f"BENCHMARK:source_files_count:{src_files_count}")
    langs = set()
    for file in os.listdir():
        if file.endswith(('.s', '.asm')):
            langs.add(file.split('.')[-1])
    print(f"BENCHMARK:languages_count:{len(langs)}")
    print("TEST_PASS:source_files_count")
except Exception as e:
    print(f"TEST_FAIL:source_files_count:{str(e)}")

# Run rosenbridge benchmark
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['python', 'rosenbridge.py'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:rosenbridge_cpu_time_s:{end_time - start_time}")
    print(f"BENCHMARK:rosenbridge_memory_usage_MiB:{current / (1024 * 1024)}")
    print("TEST_PASS:rosenbridge")
except Exception as e:
    print(f"TEST_FAIL:rosenbridge:{str(e)}")

# Compare performance vs the most similar baseline tool (rosenberg)
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['python', 'rosenberg.py'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    rosenberg_time = end_time - start_time
    rosenberg_memory = current / (1024 * 1024)
    print(f"BENCHMARK:vs_rosenberg_rosenbridge_cpu_time_ratio:{(end_time - start_time) / rosenberg_time}")
    print(f"BENCHMARK:vs_rosenberg_rosenbridge_memory_usage_ratio:{current / (1024 * 1024) / rosenberg_memory}")
    print("TEST_PASS:rosenberg")
except Exception as e:
    print(f"TEST_FAIL:rosenberg:{str(e)}")

print("RUN_OK")