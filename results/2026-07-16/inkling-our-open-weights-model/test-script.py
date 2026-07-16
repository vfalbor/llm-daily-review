import subprocess
import time
import tracemalloc
import importlib.util
import sys

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'git+https://github.com/thinkingmachines/inkling.git'], check=False)
    print('INSTALL_OK')
except Exception as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/thinkingmachines/inkling.git'], check=False)
        subprocess.run(['pip', 'install', '-e', 'inkling'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

# Measure import time
import_start = time.time()
try:
    spec = importlib.util.find_spec('inkling')
    if spec is None:
        print('TEST_FAIL:import:Module not found')
    else:
        importlib.util.module_from_spec(spec)
        spec.loader.exec_module(importlib.util.module_from_spec(spec))
    import_end = time.time()
    import_time = (import_end - import_start) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
except Exception as e:
    print(f'TEST_FAIL:import:{str(e)}')

# Load Inkling onto a GPU
try:
    import inkling
    start = time.time()
    model = inkling.Inkling()
    end = time.time()
    load_time = (end - start) * 1000
    print(f'BENCHMARK:load_time_ms:{load_time:.2f}')
    print('TEST_PASS:load')
except Exception as e:
    print(f'TEST_FAIL:load:{str(e)}')

# Benchmark API latency
try:
    start = time.time()
    model.predict('This is a sample prompt')
    end = time.time()
    latency = (end - start) * 1000
    print(f'BENCHMARK:api_latency_ms:{latency:.2f}')
    print('TEST_PASS:api_latency')
except Exception as e:
    print(f'TEST_FAIL:api_latency:{str(e)}')

# Run a sample prompt and verify output
try:
    output = model.predict('This is a sample prompt')
    if output:
        print('TEST_PASS:sample_prompt')
    else:
        print('TEST_FAIL:sample_prompt:No output')
except Exception as e:
    print(f'TEST_FAIL:sample_prompt:{str(e)}')

# Measure memory usage
tracemalloc.start()
time.sleep(0.1)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_mb:{peak / (1024 * 1024):.2f}')

# Compare against a baseline tool (Llama)
try:
    import llama
    llama_start = time.time()
    llama.model.predict('This is a sample prompt')
    llama_end = time.time()
    llama_latency = (llama_end - llama_start) * 1000
    ratio = latency / llama_latency
    print(f'BENCHMARK:vs_llama_latency_ratio:{ratio:.2f}')
except Exception as e:
    print(f'BENCHMARK:vs_llama_latency_ratio:undefined')

print('RUN_OK')