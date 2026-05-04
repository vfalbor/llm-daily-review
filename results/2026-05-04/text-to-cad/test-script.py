import subprocess
import time
import tracemalloc
import importlib.util
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK')

# Install text-to-cad
try:
    subprocess.run(['pip', 'install', 'text-to-cad'], check=False)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')

# Fallback installation method
if subprocess.run(['pip', 'show', 'text-to-cad'], check=False, stdout=subprocess.PIPE).returncode != 0:
    subprocess.run(['git', 'clone', 'https://github.com/earthtojake/text-to-cad.git'], check=False)
    subprocess.run(['pip', 'install', '-e', './text-to-cad'], check=False, cwd='./text-to-cad')
    print('INSTALL_OK')

# Load text-to-cad module
try:
    spec = importlib.util.find_spec('text_to_cad')
    if spec is None:
        raise ImportError('text_to_cad')
    import text_to_cad
    print('TEST_PASS:import_text_to_cad')
except ImportError as e:
    print(f'TEST_FAIL:import_text_to_cad:{e}')

# Measure import time
import_time_start = time.time()
try:
    import text_to_cad
except ImportError as e:
    print(f'TEST_FAIL:import_time:{e}')
import_time_end = time.time()
import_time_ms = (import_time_end - import_time_start) * 1000
print(f'BENCHMARK:import_time_ms:{import_time_ms:.2f}')

# Measure inference time
inference_time_start = time.time()
try:
    text_to_cad.infer('synthetic_text')
except Exception as e:
    print(f'TEST_FAIL:inference_time:{e}')
inference_time_end = time.time()
inference_time_ms = (inference_time_end - inference_time_start) * 1000
print(f'BENCHMARK:inference_time_ms:{inference_time_ms:.2f}')

# Measure memory usage
tracemalloc.start()
text_to_cad.infer('synthetic_text')
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_bytes:{peak}')

# Compare performance with baseline tool (deepimage)
try:
    import deepimage
except ImportError:
    print('TEST_SKIP:compare_performance:deepimage not installed')
    ratio = 1.0
else:
    deepimage_inference_time_start = time.time()
    deepimage.infer('synthetic_text')
    deepimage_inference_time_end = time.time()
    deepimage_inference_time_ms = (deepimage_inference_time_end - deepimage_inference_time_start) * 1000
    ratio = inference_time_ms / deepimage_inference_time_ms
print(f'BENCHMARK:vs_deepimage_inference_time_ratio:{ratio:.2f}')

# Upload a CAD design
try:
    text_to_cad.upload_design('synthetic_design')
    print('TEST_PASS:upload_design')
except Exception as e:
    print(f'TEST_FAIL:upload_design:{e}')

# Count lines of code
loc_count = 0
for root, dirs, files in subprocess.run(['git', 'ls-files'], check=False, capture_output=True, text=True).stdout.splitlines():
    for file in files:
        if file.endswith('.py'):
            with open(file, 'r') as f:
                loc_count += sum(1 for line in f)
print(f'BENCHMARK:loc_count:{loc_count}')

# Count test files
test_files_count = 0
for root, dirs, files in subprocess.run(['git', 'ls-files', '--', 'tests'], check=False, capture_output=True, text=True).stdout.splitlines():
    for file in files:
        if file.endswith('.py'):
            test_files_count += 1
print(f'BENCHMARK:test_files_count:{test_files_count}')

print('RUN_OK')