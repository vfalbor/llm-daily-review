import subprocess
import importlib
import time
import tracemalloc
import sys

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone Daala repository
try:
    subprocess.run(['git', 'clone', 'https://code.videolan.org/videolan/dav2d'], check=True)
except subprocess.CalledProcessError:
    print('INSTALL_FAIL:git_clone_failed')
    sys.exit(1)

# Build Daala from source
try:
    subprocess.run(['mkdir', '-p', 'dav2d/build'], check=True)
    subprocess.run(['cmake', '-S', 'dav2d', '-B', 'dav2d/build'], check=True)
    subprocess.run(['cmake', '--build', 'dav2d/build'], check=True)
except subprocess.CalledProcessError:
    print('INSTALL_FAIL:build_failed')
    sys.exit(1)

# Try building with different compiler flags
try:
    subprocess.run(['mkdir', '-p', 'dav2d/build_debug'], check=True)
    subprocess.run(['cmake', '-S', 'dav2d', '-B', 'dav2d/build_debug', '-DCMAKE_BUILD_TYPE=DEBUG'], check=True)
    subprocess.run(['cmake', '--build', 'dav2d/build_debug'], check=True)
    print('TEST_PASS:build_with_debug_flags')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:build_with_debug_flags:{str(e)}')

try:
    subprocess.run(['mkdir', '-p', 'dav2d/build_release'], check=True)
    subprocess.run(['cmake', '-S', 'dav2d', '-B', 'dav2d/build_release', '-DCMAKE_BUILD_TYPE=RELEASE'], check=True)
    subprocess.run(['cmake', '--build', 'dav2d/build_release'], check=True)
    print('TEST_PASS:build_with_release_flags')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:build_with_release_flags:{str(e)}')

# Measure import time
start_import_time = time.time()
try:
    import dav2d
except ImportError:
    print('INSTALL_FAIL:import_failed')
    sys.exit(1)
end_import_time = time.time()
import_time = (end_import_time - start_import_time) * 1000
print(f'BENCHMARK:import_time_ms:{import_time}')

# Measure video encoding/decoding benchmark
start_encoding_time = time.time()
try:
    dav2d.encode('input.mp4', 'output.mp4')
    dav2d.decode('input.mp4', 'output.mp4')
except Exception as e:
    print(f'TEST_FAIL:video_encoding_decoding:{str(e)}')
end_encoding_time = time.time()
encoding_time = (end_encoding_time - start_encoding_time) * 1000
print(f'BENCHMARK:video_encoding_decoding_ms:{encoding_time}')

# Measure memory usage
tracemalloc.start()
try:
    dav2d.encode('input.mp4', 'output.mp4')
    dav2d.decode('input.mp4', 'output.mp4')
finally:
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}')

# Compare performance with Daala
start_daala_time = time.time()
try:
    import daala
    daala.encode('input.mp4', 'output.mp4')
    daala.decode('input.mp4', 'output.mp4')
except ImportError:
    print('TEST_SKIP:daala_comparison:no_daala_module')
    daala_time = 0
else:
    end_daala_time = time.time()
    daala_time = (end_daala_time - start_daala_time) * 1000
    print(f'BENCHMARK:vs_daala_encoding_decoding_ratio:{encoding_time / daala_time}')

# Measure file count
file_count = len(subprocess.check_output(['find', 'dav2d', '-type', 'f']).decode('utf-8').splitlines())
print(f'BENCHMARK:file_count:{file_count}')

# Measure directory count
dir_count = len(subprocess.check_output(['find', 'dav2d', '-type', 'd']).decode('utf-8').splitlines())
print(f'BENCHMARK:dir_count:{dir_count}')

# Measure line of code count
loc_count = 0
for line in subprocess.check_output(['find', 'dav2d', '-type', 'f', '-name', '*.c', '-o', '-name', '*.cpp', '-o', '-name', '*.h']).decode('utf-8').splitlines():
    loc_count += len(subprocess.check_output(['wc', '-l', line]).decode('utf-8').splitlines()[0].split()[0])
print(f'BENCHMARK:loc_count:{loc_count}')

print('RUN_OK')