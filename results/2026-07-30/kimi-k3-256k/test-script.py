import subprocess
import time
import tracemalloc
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

try:
    # Install kimi via pip
    subprocess.run(['pip', 'install', 'kimi'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError:
    try:
        # Install kimi via git clone and pip install -e
        subprocess.run(['git', 'clone', 'https://github.com/kimi-code/kimi.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './kimi'], check=True, cwd='./kimi')
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{str(e)}')

try:
    import kimi
except ImportError:
    print('TEST_FAIL:import_kimi:unable to import kimi')
else:
    # Measure import time
    import_time = time.time()
    import kimi
    import_time = time.time() - import_time
    print(f'BENCHMARK:import_time_ms:{import_time * 1000}')

# Test 1: Train the model on a synthetic dataset
try:
    tracemalloc.start()
    start_time = time.time()
    model = kimi.Model()
    model.train([['synthetic', 'data']])
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print('TEST_PASS:train_model')
    print(f'BENCHMARK:train_model_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:train_model_peak_memory_mb:{peak / 1024 / 1024}')
except Exception as e:
    print(f'TEST_FAIL:train_model:{str(e)}')

# Test 2: Evaluate the model on a known benchmark
try:
    tracemalloc.start()
    start_time = time.time()
    model = kimi.Model()
    model.evaluate([['known', 'benchmark']])
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print('TEST_PASS:evaluate_model')
    print(f'BENCHMARK:evaluate_model_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:evaluate_model_peak_memory_mb:{peak / 1024 / 1024}')
except Exception as e:
    print(f'TEST_FAIL:evaluate_model:{str(e)}')

# Benchmark vs LLaMA
try:
    import llama
    llama_model = llama.Model()
    llama_start_time = time.time()
    llama_model.train([['synthetic', 'data']])
    llama_end_time = time.time()
    llama_import_time = time.time()
    import llama
    llama_import_time = time.time() - llama_import_time
    print(f'BENCHMARK:vs_llama_train_model_ratio:{(end_time - start_time) / (llama_end_time - llama_start_time)}')
    print(f'BENCHMARK:vs_llama_import_time_ratio:{import_time / llama_import_time}')
except ImportError:
    print('TEST_SKIP:benchmark_vs_llama:unable to import llama')

print('RUN_OK')