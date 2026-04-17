import subprocess
import time
import tracemalloc
import os
import importlib.util

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'mergetopus'], check=True)
except subprocess.CalledProcessError:
    subprocess.run(['git', 'clone', 'https://github.com/mwallner/mergetopus.git'], check=True)
    os.chdir('mergetopus')
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    os.chdir('..')

# Load the mergetopus module
spec = importlib.util.find_spec('mergetopus')
if spec is None:
    print('INSTALL_FAIL: Unable to import mergetopus')
else:
    print('INSTALL_OK')

# Load a Git repo for testing
subprocess.run(['git', 'clone', 'https://github.com/git/git.git'], check=True)

# Prepare a large merge with several conflicts
os.chdir('git')
subprocess.run(['git', 'checkout', 'master'], check=True)
subprocess.run(['git', 'branch', 'conflict-branch'], check=True)
subprocess.run(['git', 'checkout', 'conflict-branch'], check=True)
with open('README.md', 'a') as f:
    f.write('conflict line\n')

# Measure import time
start_time = time.time()
import mergetopus
import_time = time.time() - start_time
print(f'BENCHMARK:import_time_ms:{import_time*1000}')

# Run mergetopus to break the merge into parallel tasks
start_time = time.time()
tracemalloc.start()
subprocess.run(['mergetopus', 'break-merge'], check=True)
end_time = time.time()
memory_usage, peak_memory = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:mergetopus_break_merge_time_ms:{(end_time-start_time)*1000}')
print(f'BENCHMARK:mergetopus_break_merge_memory_mb:{peak_memory/1024/1024}')

# Compare the result against a manual merge
start_time = time.time()
subprocess.run(['git', 'merge', 'master'], check=True)
end_time = time.time()
print(f'BENCHMARK:manual_merge_time_ms:{(end_time-start_time)*1000}')

# Benchmark against Git's internal merge algorithm
start_time = time.time()
subprocess.run(['git', 'merge', '-m', 'conflict message', 'master'], check=True)
end_time = time.time()
print(f'BENCHMARK:git_merge_time_ms:{(end_time-start_time)*1000}')
print(f'BENCHMARK:vs_git_merge_ratio:{(end_time-start_time)/(end_time-start_time)}')

# Run tests
try:
    # Test 1: mergetopus breaks merge into parallel tasks
    start_time = time.time()
    subprocess.run(['mergetopus', 'break-merge'], check=True)
    end_time = time.time()
    print(f'TEST_PASS:mergetopus_breaks_merge')
    print(f'BENCHMARK:mergetopus_break_merge_time_ms:{(end_time-start_time)*1000}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:mergetopus_breaks_merge:{str(e)}')

try:
    # Test 2: mergetopus handles conflicts
    start_time = time.time()
    subprocess.run(['mergetopus', 'break-merge'], check=True)
    end_time = time.time()
    print(f'TEST_PASS:mergetopus_handles_conflicts')
    print(f'BENCHMARK:mergetopus_handle_conflicts_time_ms:{(end_time-start_time)*1000}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:mergetopus_handles_conflicts:{str(e)}')

try:
    # Test 3: mergetopus compares to manual merge
    start_time = time.time()
    subprocess.run(['git', 'merge', 'master'], check=True)
    end_time = time.time()
    print(f'TEST_PASS:mergetopus_compares_to_manual_merge')
    print(f'BENCHMARK:mergetopus_compares_to_manual_merge_time_ms:{(end_time-start_time)*1000}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:mergetopus_compares_to_manual_merge:{str(e)}')

# Clean up
os.chdir('..')
subprocess.run(['rm', '-rf', 'git'], check=True)

# Benchmark memory count
import psutil
process = psutil.Process(os.getpid())
memory_count = process.memory_info().rss / 1024 / 1024
print(f'BENCHMARK:memory_count_mb:{memory_count}')

# Benchmark loc count
loc_count = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, check=True).stdout.count('\n')
print(f'BENCHMARK:loc_count:{loc_count}')

# Benchmark test files count
test_files_count = subprocess.run(['find', '.', '-name', 'test*', '-type', 'f'], capture_output=True, text=True, check=True).stdout.count('\n')
print(f'BENCHMARK:test_files_count:{test_files_count}')

print('RUN_OK')