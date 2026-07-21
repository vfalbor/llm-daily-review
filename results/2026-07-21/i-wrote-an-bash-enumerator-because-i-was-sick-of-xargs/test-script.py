import subprocess
import time
import tracemalloc
import sys

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)

# Install Bash Enumerators using pip
start_time = time.time()
try:
    subprocess.run(['pip', 'install', 'bash-enumerators'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')
    # Fallback: git clone and pip install -e
    subprocess.run(['git', 'clone', 'https://github.com/numerlab/bash-enumerators.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './bash-enumerators'], cwd='./bash-enumerators', check=True)
    print('INSTALL_OK')
end_time = time.time()
print(f'BENCHMARK:install_time_s:{end_time - start_time}')

# Run example script
start_time = time.time()
try:
    subprocess.run(['bash', './bash-enumerators/example.sh'], check=True)
    print('TEST_PASS:example_script')
except Exception as e:
    print(f'TEST_FAIL:example_script:{str(e)}')
end_time = time.time()
print(f'BENCHMARK:example_script_time_ms:{(end_time - start_time) * 1000}')

# Compare enumeration speeds of bash-enumerators and xargs
start_time = time.time()
subprocess.run(['bash', './bash-enumerators/example.sh', '--enumerate'], check=True)
end_time = time.time()
bash_time = end_time - start_time

start_time = time.time()
subprocess.run(['xargs', '-n', '1', 'echo'], input='1 2 3 4 5', check=True)
end_time = time.time()
xargs_time = end_time - start_time

print(f'BENCHMARK:vs_xargs_enumeration_time_ms:{(bash_time / xargs_time) * 1000}')

# Write a Bash function and parse arguments with Bash enumerators
start_time = time.time()
try:
    subprocess.run(['bash', './bash-enumerators/example.sh', '--parse-args'], check=True)
    print('TEST_PASS:parse_args')
except Exception as e:
    print(f'TEST_FAIL:parse_args:{str(e)}')
end_time = time.time()
print(f'BENCHMARK:parse_args_time_ms:{(end_time - start_time) * 1000}')

# Measure peak memory usage
tracemalloc.start()
subprocess.run(['bash', './bash-enumerators/example.sh'], check=True)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:peak_memory_usage_mb:{peak / (1024 * 1024)}')

# Measure number of test files
try:
    output = subprocess.check_output(['git', 'ls-files', '--', '*.sh'], cwd='./bash-enumerators').decode('utf-8')
    print(f'BENCHMARK:test_files_count:{len(output.splitlines())}')
except Exception as e:
    print(f'TEST_FAIL:count_test_files:{str(e)}')

print('RUN_OK')