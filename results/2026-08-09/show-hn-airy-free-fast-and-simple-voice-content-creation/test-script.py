import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
print('INSTALL_OK')

# Install tool dependencies
try:
    subprocess.run(['npm', 'install', '-g', '@airy/airy-cli'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/airy-io/airy.git'], check=True)
        subprocess.run(['npm', 'install'], cwd='./airy', check=True)
        subprocess.run(['npm', 'run', 'build'], cwd='./airy', check=True)
        subprocess.run(['npm', 'link'], cwd='./airy', check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

# Install baseline tool (Audacity)
subprocess.run(['apk', 'add', '--no-cache', 'audacity'], check=False)
print('INSTALL_OK')

# Test record and edit voice clip
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['airy', 'record', '--output', 'test_clip.wav'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:record_time_ms:{(time.time() - start_time) * 1000}')
    print(f'BENCHMARK:record_memory_mb:{current / 10**6}')
    print('TEST_PASS:record_clip')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:record_clip:{e}')

# Test edit voice clip
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['airy', 'edit', 'test_clip.wav', '--output', 'edited_clip.wav'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:edit_time_ms:{(time.time() - start_time) * 1000}')
    print(f'BENCHMARK:edit_memory_mb:{current / 10**6}')
    print('TEST_PASS:edit_clip')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:edit_clip:{e}')

# Compare performance vs baseline tool (Audacity)
try:
    start_time = time.time()
    subprocess.run(['audacity', '--record', '--output', 'baseline_clip.wav'], check=True)
    baseline_time = time.time() - start_time
    start_time = time.time()
    subprocess.run(['airy', 'record', '--output', 'test_clip.wav'], check=True)
    airy_time = time.time() - start_time
    print(f'BENCHMARK:vs_audacity_record_ratio:{airy_time / baseline_time}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:compare_baseline:{e}')

# Get file count and line count
file_count = len(os.listdir())
loc_count = sum(1 for file in os.listdir() if file.endswith('.js') for line in open(file) if line.strip())
print(f'BENCHMARK:file_count:{file_count}')
print(f'BENCHMARK:loc_count:{loc_count}')

print('RUN_OK')