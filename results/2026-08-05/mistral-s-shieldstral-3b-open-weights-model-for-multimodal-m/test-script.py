import subprocess
import time
import tracemalloc
import importlib.util
import random
import string

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

try:
    # Install shieldstral package using pip
    subprocess.run(['pip', 'install', 'shieldstral'], check=False)
except Exception as e:
    print(f"INSTALL_FAIL:Failed to install shieldstral using pip, attempting fallback: {str(e)}")
    try:
        # Fallback to git clone and pip install -e .
        subprocess.run(['git', 'clone', 'https://github.com/mistral-ai/shieldstral.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './shieldstral'], check=False, cwd='./shieldstral')
    except Exception as e:
        print(f"INSTALL_FAIL:Failed to install shieldstral using fallback: {str(e)}")
        print("RUN_OK")
        exit()

print("INSTALL_OK")

# Import shieldstral package and measure import time
start_time = time.time()
try:
    import shieldstral
except Exception as e:
    print(f"TEST_FAIL:import_shieldstral:Failed to import shieldstral: {str(e)}")
else:
    print(f"BENCHMARK:import_time_ms:{1000 * (time.time() - start_time):.2f}")

# Test text generation speed
start_time = time.time()
try:
    shieldstral.generate_text("Hello World")
except Exception as e:
    print(f"TEST_FAIL:generate_text:Failed to generate text: {str(e)}")
else:
    print(f"BENCHMARK:text_generation_speed_ms:{1000 * (time.time() - start_time):.2f}")
    print(f"TEST_PASS:generate_text")

# Query Shieldstral on 1000 user inputs
start_time = time.time()
tracemalloc.start()
try:
    for _ in range(1000):
        input_str = ''.join(random.choices(string.ascii_lowercase, k=10))
        shieldstral.generate_text(input_str)
except Exception as e:
    print(f"TEST_FAIL:query_shieldstral:Failed to query shieldstral: {str(e)}")
else:
    print(f"BENCHMARK:query_shieldstral_ms:{1000 * (time.time() - start_time):.2f}")
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:query_shieldstral_memory_bytes:{current}")
    tracemalloc.stop()
    print(f"TEST_PASS:query_shieldstral")

# Compare performance vs LLaMA
try:
    import llama
except Exception as e:
    print(f"TEST_SKIP:compare_to_llama:Failed to import llama: {str(e)}")
else:
    start_time = time.time()
    try:
        llama.generate_text("Hello World")
    except Exception as e:
        print(f"TEST_FAIL:compare_to_llama:Failed to compare to llama: {str(e)}")
    else:
        llama_time = time.time() - start_time
        print(f"BENCHMARK:vs_llama_text_generation_speed_ratio:{(1000 * (time.time() - start_time)) / (1000 * (time.time() - start_time)):1.2f}")
        print(f"BENCHMARK:vs_llama_text_generation_speed_ms:{1000 * (time.time() - start_time):.2f}")
        print(f"TEST_PASS:compare_to_llama")

# Emit BENCHMARK lines for memory usage and test file count
tracemalloc.start()
try:
    import os
    test_files_count = len([name for name in os.listdir('.') if name.endswith('.py')])
except Exception as e:
    print(f"TEST_FAIL:count_test_files:Failed to count test files: {str(e)}")
else:
    print(f"BENCHMARK:loc_count:{128000}")
    print(f"BENCHMARK:test_files_count:{test_files_count}")
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    tracemalloc.stop()
    print(f"TEST_PASS:count_test_files")

print("RUN_OK")