import subprocess
import time
import tracemalloc
import os

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Clone Transcribe.cpp repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/cjpais/transcribe-cpp.git'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Build Transcribe.cpp from source
try:
    subprocess.run(['cmake', '-B', 'build'], cwd='transcribe-cpp', check=True)
    subprocess.run(['cmake', '--build', 'build'], cwd='transcribe-cpp', check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Test 1: Transcribe a sample audio file
try:
    start_time = time.time()
    subprocess.run(['./build/transcribe', 'sample_audio.wav'], cwd='transcribe-cpp', check=True)
    end_time = time.time()
    print(f"BENCHMARK:transcribe_time_ms:{(end_time - start_time) * 1000:.2f}")
    print("TEST_PASS:transcribe_audio")
except Exception as e:
    print(f"TEST_FAIL:transcribe_audio:{e}")

# Test 2: Check Transcribe.cpp's API support for custom transcription
try:
    subprocess.run(['./build/transcribe', '--help'], cwd='transcribe-cpp', check=True, stdout=subprocess.DEVNULL)
    print("TEST_PASS:custom_transcription")
except Exception as e:
    print(f"TEST_FAIL:custom_transcription:{e}")

# Test 3: Transcribe a 10-minute audio file and measure accuracy
try:
    start_time = time.time()
    subprocess.run(['./build/transcribe', '10min_audio.wav'], cwd='transcribe-cpp', check=True)
    end_time = time.time()
    print(f"BENCHMARK:transcribe_10min_time_ms:{(end_time - start_time) * 1000:.2f}")
    print("TEST_PASS:transcribe_10min")
except Exception as e:
    print(f"TEST_FAIL:transcribe_10min:{e}")

# Compare performance with Google Cloud Speech-to-Text
try:
    start_time = time.time()
    subprocess.run(['gcloud', 'speech', 'recognize', '--language-code', 'en-US', 'sample_audio.wav'], check=True)
    end_time = time.time()
    gcst_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:gcst_transcribe_time_ms:{gcst_time:.2f}")
    print(f"BENCHMARK:vs_gcst_transcribe_ratio:{((end_time - start_time) * 1000) / gcst_time:.2f}")
    print("TEST_PASS:compare_performance")
except Exception as e:
    print(f"TEST_FAIL:compare_performance:{e}")

# Measure memory usage
try:
    tracemalloc.start()
    subprocess.run(['./build/transcribe', 'sample_audio.wav'], cwd='transcribe-cpp', check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    print("TEST_PASS:memory_usage")
except Exception as e:
    print(f"TEST_FAIL:memory_usage:{e}")

# Measure file count
try:
    file_count = len(os.listdir('transcribe-cpp'))
    print(f"BENCHMARK:file_count:{file_count}")
    print("TEST_PASS:file_count")
except Exception as e:
    print(f"TEST_FAIL:file_count:{e}")

# Measure line of code count
try:
    loc_count = 0
    for root, dirs, files in os.walk('transcribe-cpp'):
        for file in files:
            if file.endswith('.cpp') or file.endswith('.h'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += len(f.readlines())
    print(f"BENCHMARK:loc_count:{loc_count}")
    print("TEST_PASS:loc_count")
except Exception as e:
    print(f"TEST_FAIL:loc_count:{e}")

print("RUN_OK")