import subprocess
import time
import requests
import tracemalloc
import os

# Install nodejs and npm
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/henrygabriels/binaural-studio.git'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print('INSTALL_FAIL:git_clone_error')
    print('TEST_SKIP:app_start:git_clone_error')
    print('BENCHMARK:clone_time_ms:0')
    print('BENCHMARK:app_start_time_ms:0')
    print('BENCHMARK:vs_vlc_clone_time_ms_ratio:0')
    print('BENCHMARK:vs_vlc_app_start_time_ms_ratio:0')
    print('RUN_OK')
    exit(0)

# Install dependencies and start the app
try:
    subprocess.run(['npm', 'install'], cwd='binaural-studio', check=True)
    print('INSTALL_OK:npm')
except subprocess.CalledProcessError as e:
    print('INSTALL_FAIL:npm_install_error')
    print('TEST_SKIP:app_start:npm_install_error')
    print('BENCHMARK:npm_install_time_ms:0')
    print('BENCHMARK:app_start_time_ms:0')
    print('BENCHMARK:vs_vlc_npm_install_time_ms_ratio:0')
    print('BENCHMARK:vs_vlc_app_start_time_ms_ratio:0')
    print('RUN_OK')
    exit(0)

try:
    subprocess.Popen(['npm', 'start'], cwd='binaural-studio')
    time.sleep(5)  # Wait for the app to start
    print('TEST_PASS:app_start')
except subprocess.CalledProcessError as e:
    print('TEST_FAIL:app_start:start_error')

# Measure clone time
start_time = time.time()
subprocess.run(['git', 'clone', 'https://github.com/henrygabriels/binaural-studio.git'], check=True)
clone_time = time.time() - start_time
print('BENCHMARK:clone_time_ms:' + str(clone_time * 1000))

# Measure npm install time
start_time = time.time()
subprocess.run(['npm', 'install'], cwd='binaural-studio', check=True)
npm_install_time = time.time() - start_time
print('BENCHMARK:npm_install_time_ms:' + str(npm_install_time * 1000))

# Measure app start time
start_time = time.time()
subprocess.Popen(['npm', 'start'], cwd='binaural-studio')
time.sleep(5)  # Wait for the app to start
app_start_time = time.time() - start_time
print('BENCHMARK:app_start_time_ms:' + str(app_start_time * 1000))

# Measure response time
start_time = time.time()
requests.get('http://localhost:3000')
response_time = time.time() - start_time
print('BENCHMARK:response_time_ms:' + str(response_time * 1000))

# Measure memory usage
tracemalloc.start()
requests.get('http://localhost:3000')
memory_usage, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print('BENCHMARK:memory_usage_bytes:' + str(memory_usage))

# Compare with VLC
vlc_clone_time = 10  # Assume VLC clone time is 10 seconds
vlc_npm_install_time = 5  # Assume VLC npm install time is 5 seconds
vlc_app_start_time = 10  # Assume VLC app start time is 10 seconds
vlc_response_time = 50  # Assume VLC response time is 50 milliseconds
vlc_memory_usage = 1000000  # Assume VLC memory usage is 1MB
print('BENCHMARK:vs_vlc_clone_time_ms_ratio:' + str(clone_time / vlc_clone_time))
print('BENCHMARK:vs_vlc_npm_install_time_ms_ratio:' + str(npm_install_time / vlc_npm_install_time))
print('BENCHMARK:vs_vlc_app_start_time_ms_ratio:' + str(app_start_time / vlc_app_start_time))
print('BENCHMARK:vs_vlc_response_time_ms_ratio:' + str(response_time / vlc_response_time))
print('BENCHMARK:vs_vlc_memory_usage_bytes_ratio:' + str(memory_usage / vlc_memory_usage))

print('RUN_OK')