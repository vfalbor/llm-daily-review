import subprocess
import time
import tracemalloc
import sys

# Install system packages
print("Installing system packages...")
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Install Kokoro using pip
print("Installing Kokoro using pip...")
try:
    subprocess.run(['pip', 'install', 'kokoro'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/llm-ai/kokoro.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './kokoro'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

# Import Kokoro and measure import time
print("Importing Kokoro and measuring import time...")
start_time = time.time()
try:
    import kokoro
    end_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_kokoro:{str(e)}")

# Generate 1000 text-to-speech pairs and measure latency
print("Generating 1000 text-to-speech pairs and measuring latency...")
try:
    start_time = time.time()
    for i in range(1000):
        text = f"Hello world {i}"
        audio = kokoro.generate_audio(text)
    end_time = time.time()
    print(f"BENCHMARK:generate_audio_latency_ms:{(end_time - start_time) * 1000 / 1000:.2f}")
    print("TEST_PASS:generate_audio")
except Exception as e:
    print(f"TEST_FAIL:generate_audio:{str(e)}")

# Compare performance vs Naver's TTS (baseline tool)
print("Comparing performance vs Naver's TTS...")
try:
    import naver_tts
    start_time = time.time()
    for i in range(1000):
        text = f"Hello world {i}"
        audio = naver_tts.generate_audio(text)
    end_time = time.time()
    naver_latencies = (end_time - start_time) * 1000 / 1000
    kokoro_latencies = (end_time - start_time) * 1000 / 1000
    ratio = kokoro_latencies / naver_latencies
    print(f"BENCHMARK:vs_naver_tts_latency_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_SKIP:compare_performance_vs_naver_tts:{str(e)}")

# Measure memory usage
print("Measuring memory usage...")
try:
    tracemalloc.start()
    import kokoro
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{peak:.2f}")
    tracemalloc.stop()
except Exception as e:
    print(f"TEST_FAIL:measure_memory_usage:{str(e)}")

# Measure number of lines of code
print("Measuring number of lines of code...")
try:
    subprocess.run(['git', 'clone', 'https://github.com/llm-ai/kokoro.git'], check=True)
    lines_of_code = subprocess.run(['wc', '-l', './kokoro'], capture_output=True, text=True).stdout.split()[0]
    print(f"BENCHMARK:loc_count:{lines_of_code}")
except Exception as e:
    print(f"TEST_FAIL:measure_loc_count:{str(e)}")

# Measure number of test files
print("Measuring number of test files...")
try:
    subprocess.run(['git', 'clone', 'https://github.com/llm-ai/kokoro.git'], check=True)
    test_files = subprocess.run(['find', './kokoro', '-name', '*.py'], capture_output=True, text=True).stdout.splitlines()
    print(f"BENCHMARK:test_files_count:{len(test_files)}")
except Exception as e:
    print(f"TEST_FAIL:measure_test_files_count:{str(e)}")

print("RUN_OK")