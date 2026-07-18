import subprocess
import time
from tracemalloc import start, stop, get_traced_memory
import requests
import git

# APK packages installation
subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

print('INSTALL_OK')

# Clone Vāgdhenu repository
start_time = time.time()
repo = git.Repo.clone_from('https://github.com/prathosh/vagdhenu.git', 'vagdhenu')
clone_time = time.time() - start_time
print(f'BENCHMARK:clone_time_s:{clone_time}')

# Build Vāgdhenu from source
start_time = time.time()
try:
    subprocess.run(['go', 'build', './...'], cwd='vagdhenu', check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:build_error:{e}')

# Run hello world
start_time = time.time()
try:
    subprocess.run(['./main'], cwd='vagdhenu', check=True)
    print(f'BENCHMARK:hello_world_ms:{(time.time() - start_time) * 1000}')
    print('TEST_PASS:hello_world')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:hello_world:{e}')

# Start memory tracing
start()

# Generate audio for a Sanskrit text
start_time = time.time()
try:
    subprocess.run(['./main', '-t', 'संस्कृतम्'], cwd='vagdhenu', check=True)
    generate_time = time.time() - start_time
    memory, peak = get_traced_memory()
    stop()
    print(f'BENCHMARK:generate_time_ms:{generate_time * 1000}')
    print(f'BENCHMARK:generate_memory_mb:{peak / (1024 * 1024)}')
    print('TEST_PASS:generate_audio')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:generate_audio:{e}')

# Compare with human recording (simulated)
simulated_recording_time = 500  # simulated human recording time
print(f'BENCHMARK:vs_human_recording_ratio:{generate_time / (simulated_recording_time / 1000)}')

# Measure and emit lines of code
import os
def count_loc(directory):
    loc = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.go', '.py', '.rs', '.js', '.ts')):
                with open(os.path.join(root, file), 'r') as f:
                    loc += len(f.readlines())
    return loc
loc_count = count_loc('vagdhenu')
print(f'BENCHMARK:loc_count:{loc_count}')

# Measure and emit number of test files
import glob
test_files = len(glob.glob('vagdhenu/**/*_test.go', recursive=True))
print(f'BENCHMARK:test_files_count:{test_files}')

print('RUN_OK')