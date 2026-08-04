import subprocess
import time
import tracemalloc
import importlib.util
import sys
import os

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:apk_add_failed:{e}')
    sys.exit(1)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'torch', 'transformers'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:pip_install_failed:{e}')
    try:
        subprocess.run(['git', 'clone', 'https://github.com/MakazhanAlpamys/Soup'], check=True)
        subprocess.run(['pip', 'install', '-e', './Soup'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:git_clone_and_pip_install_failed:{e}')
        sys.exit(1)

# Import the package and measure import time
start_time = time.time()
try:
    spec = importlib.util.find_spec('Soup')
    if spec is None:
        raise ImportError
    import Soup
except ImportError as e:
    print(f'TEST_FAIL:import_failed:{e}')
else:
    print(f'TEST_PASS:import')
    import_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time:.2f}')

# Test fine-tune model on a 4 GB GPU
try:
    start_time = time.time()
    Soup.fine_tune_model()
    fine_tune_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:fine_tune_time_ms:{fine_tune_time:.2f}')
    print('TEST_PASS:fine_tune_model')
except Exception as e:
    print(f'TEST_FAIL:fine_tune_model:{e}')

# Test evaluate on a dataset
try:
    start_time = time.time()
    Soup.evaluate()
    evaluate_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:evaluate_time_ms:{evaluate_time:.2f}')
    print('TEST_PASS:evaluate')
except Exception as e:
    print(f'TEST_FAIL:evaluate:{e}')

# Compare with a baseline model
try:
    import transformers
    start_time = time.time()
    transformers.modeling_utils.PreTrainedModel
    baseline_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:vs_transformers_import_time_ms:{baseline_time:.2f}')
    ratio = import_time / baseline_time
    print(f'BENCHMARK:vs_transformers_import_time_ratio:{ratio:.2f}')
    print('TEST_PASS:compare_with_baseline')
except Exception as e:
    print(f'TEST_FAIL:compare_with_baseline:{e}')

# Measure memory usage
tracemalloc.start()
Soup.fine_tune_model()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_bytes:{current}')
print(f'BENCHMARK:peak_memory_usage_bytes:{peak}')

# Measure number of lines of code
with open('setup.py', 'r') as f:
    lines = f.readlines()
print(f'BENCHMARK:loc_count:{len(lines)}')

# Measure number of test files
test_files = os.listdir('tests')
print(f'BENCHMARK:test_files_count:{len(test_files)}')

print('RUN_OK')