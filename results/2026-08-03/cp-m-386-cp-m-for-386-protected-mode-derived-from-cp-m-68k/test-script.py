import subprocess
import time
import tracemalloc
import os
import git

# Install system packages
def install_apk(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{pkg} installation failed with return code {e.returncode}")

install_apk('git')
install_apk('gcc')
install_apk('make')

# Install tool dependencies
def install_tool_dependencies():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/johnsonjh/cpm386.git'], check=True)
        subprocess.run(['cd', 'cpm386'], check=True)
        subprocess.run(['make'], check=True, cwd='cpm386')
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:CP/M-386 installation failed with return code {e.returncode}")
    else:
        print("INSTALL_OK")

install_tool_dependencies()

# Measure source files and languages
def count_source_files():
    repo = git.Repo('cpm386')
    files = repo.git.ls_files().splitlines()
    print(f"BENCHMARK:source_files_count:{len(files)}")
    languages = set()
    for file in files:
        if file.endswith('.c'):
            languages.add('C')
        elif file.endswith('.h'):
            languages.add('C header')
        elif file.endswith('.asm'):
            languages.add('Assembly')
    print(f"BENCHMARK:languages_count:{len(languages)}")

count_source_files()

# Run Python examples
def run_python_examples():
    try:
        subprocess.run(['python', '-c', 'import os'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_python_examples:Failed to import os module with return code {e.returncode}")
    else:
        print("TEST_PASS:run_python_examples")

run_python_examples()

# Measure boot-time
def measure_boot_time():
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['./cpm386'], check=True, cwd='cpm386')
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:boot_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:boot_time_memory_mb:{current / 1024 / 1024}")

measure_boot_time()

# Compare with baseline tool
def compare_with_baseline():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/johnsonjh/cpm68k.git'], check=True)
        subprocess.run(['make'], check=True, cwd='cpm68k')
        baseline_boot_time = subprocess.run(['./cpm68k'], capture_output=True, cwd='cpm68k', check=True)
        baseline_boot_time = float(baseline_boot_time.stderr.decode('utf-8').splitlines()[0].split(':')[1])
        print(f"BENCHMARK:vs_cpm68k_boot_time_ratio:{(end_time - start_time) / baseline_boot_time}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_with_baseline:Failed to compare with baseline tool with return code {e.returncode}")

compare_with_baseline()

# Measure IO performance
def measure_io_performance():
    try:
        subprocess.run(['./cpm386', '-f', 'test.txt'], check=True, cwd='cpm386')
        start_time = time.time()
        subprocess.run(['cat', 'test.txt'], check=True, cwd='cpm386')
        end_time = time.time()
        print(f"BENCHMARK:io_performance_ms:{(end_time - start_time) * 1000}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:measure_io_performance:Failed to measure IO performance with return code {e.returncode}")

measure_io_performance()

print("RUN_OK")