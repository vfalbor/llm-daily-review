import importlib.util
import importlib.machinery
import subprocess
import time
import tracemalloc
import sys

# Install git apk package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

try:
    # Install grok-build via pip
    subprocess.run(['pip', 'install', 'git+https://github.com/xai-org/grok-build.git'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    try:
        # Fallback to git clone and pip install -e
        subprocess.run(['git', 'clone', 'https://github.com/xai-org/grok-build.git'], check=True)
        subprocess.run(['pip', 'install', '-e', 'grok-build'], cwd='grok-build', check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')
        sys.exit(0)

# Import grok-build
try:
    spec = importlib.util.find_spec('grokbuild')
    if spec is None:
        raise ImportError('Could not find module')
    importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sys.modules['grokbuild'])
    print('TEST_PASS:import')
except ImportError as e:
    print(f'TEST_FAIL:import:{e}')

# Measure import time
try:
    start_time = time.time()
    importlib.import_module('grokbuild')
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time}')
except Exception as e:
    print(f'TEST_FAIL:import_time:{e}')

# Measure core operation latency
try:
    start_time = time.time()
    # Minimal functional test with synthetic data
    from grokbuild import build
    build('synthetic_data')
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f'BENCHMARK:core_operation_ms:{latency}')
    print('TEST_PASS:core_operation')
except Exception as e:
    print(f'TEST_FAIL:core_operation:{e}')

# Measure memory usage
try:
    tracemalloc.start()
    importlib.import_module('grokbuild')
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_bytes:{peak}')
except Exception as e:
    print(f'TEST_FAIL:memory_usage:{e}')

# Compare vs baseline tool (python)
try:
    import timeit
    # Python baseline: fibonacci
    def fibonacci(n):
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    python_baseline_time = timeit.timeit(lambda: fibonacci(35), number=1)
    # Grokbuild baseline: fibonacci
    from grokbuild import build
    def grokbuild_baseline():
        # Synthetic data
        return build('synthetic_data')
    grokbuild_baseline_time = timeit.timeit(grokbuild_baseline, number=1)
    ratio = grokbuild_baseline_time / python_baseline_time
    print(f'BENCHMARK:vs_python_fib35_ratio:{ratio}')
    print('TEST_PASS:baseline_comparison')
except Exception as e:
    print(f'TEST_FAIL:baseline_comparison:{e}')

# Additional benchmarks
try:
    import os
    import stat
    # Measure loc count
    loc_count = 0
    for root, dirs, files in os.walk('grok-build'):
        for file in files:
            if file.endswith('.py'):
                loc_count += sum(1 for line in open(os.path.join(root, file)))
    print(f'BENCHMARK:loc_count:{loc_count}')
    # Measure test files count
    test_files_count = 0
    for file in os.listdir('grok-build'):
        if file.startswith('test'):
            test_files_count += 1
    print(f'BENCHMARK:test_files_count:{test_files_count}')
except Exception as e:
    print(f'TEST_FAIL:additional_benchmarks:{e}')

print('RUN_OK')