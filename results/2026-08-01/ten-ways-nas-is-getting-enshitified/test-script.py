import subprocess
import sys
import time
from tracemalloc import start, stop, get_traced_memory
import importlib.util

# Install git and python dev packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'python3-dev'], check=False)

# Install tool dependencies via pip
try:
    subprocess.run(['pip', 'install', '--no-cache-dir', 'ten-ways-nas-is-getting-enshitified'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')
    try:
        subprocess.run(['git', 'clone', 'https://github.com/unknown/ten-ways-nas-is-getting-enshitified.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './ten-ways-nas-is-getting-enshitified'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')
        sys.exit(1)

# Basic run test
try:
    spec = importlib.util.find_spec('ten_ways_nas_is_getting_enshitified')
    if spec is None:
        raise ImportError
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run_synthetic_test()
    print('TEST_PASS:basic_run')
except Exception as e:
    print(f'TEST_FAIL:basic_run:{str(e)}')

# Measure performance
start_time = time.time()
try:
    import ten_ways_nas_is_getting_enshitified
    import_time_ms = (time.time() - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time_ms}')
    start_time = time.time()
    ten_ways_nas_is_getting_enshitified.run_synthetic_test()
    run_time_ms = (time.time() - start_time) * 1000
    print(f'BENCHMARK:run_time_ms:{run_time_ms}')
    start()
    ten_ways_nas_is_getting_enshitified.run_synthetic_test()
    stop()
    current, peak = get_traced_memory()
    memory_mb = peak / (1024 * 1024)
    print(f'BENCHMARK:memory_mb:{memory_mb}')
except Exception as e:
    print(f'TEST_FAIL:performance_test:{str(e)}')

# Compare vs baseline tool (no similar tools provided)
print('TEST_SKIP:baseline_comparison:No similar tools provided')

print('RUN_OK')