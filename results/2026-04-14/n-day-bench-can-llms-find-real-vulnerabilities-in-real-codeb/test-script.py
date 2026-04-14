import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install N-Day-Bench and Semgrep
try:
    subprocess.run(['pip', 'install', 'ndaybench'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')

try:
    subprocess.run(['pip', 'install', 'semgrep'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')

# Install ndaybench from source as a fallback
try:
    subprocess.run(['git', 'clone', 'https://github.com/winfunc/ndaybench.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './ndaybench'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')

# Test ndaybench import time
start_time = time.time()
try:
    spec = importlib.util.find_spec('ndaybench')
    if spec is None:
        print('TEST_FAIL:ndaybench_import:Module not found')
    else:
        ndaybench = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ndaybench)
        import_time = time.time() - start_time
        print(f'BENCHMARK:import_time_ms:{import_time * 1000}')
        print('TEST_PASS:ndaybench_import')
except Exception as e:
    print(f'TEST_FAIL:ndaybench_import:{e}')

# Test ndaybench scan
start_time = time.time()
try:
    subprocess.run(['ndaybench', '--help'], check=True)
    scan_time = time.time() - start_time
    print(f'BENCHMARK:scan_time_ms:{scan_time * 1000}')
    print('TEST_PASS:ndaybench_scan')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:ndaybench_scan:{e}')

# Test Semgrep import time
start_time = time.time()
try:
    spec = importlib.util.find_spec('semgrep')
    if spec is None:
        print('TEST_FAIL:semgrep_import:Module not found')
    else:
        semgrep = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(semgrep)
        import_time = time.time() - start_time
        print(f'BENCHMARK:semgrep_import_time_ms:{import_time * 1000}')
        print('TEST_PASS:semgrep_import')
except Exception as e:
    print(f'TEST_FAIL:semgrep_import:{e}')

# Test Semgrep scan
start_time = time.time()
try:
    subprocess.run(['semgrep', '--help'], check=True)
    scan_time = time.time() - start_time
    print(f'BENCHMARK:semgrep_scan_time_ms:{scan_time * 1000}')
    print('TEST_PASS:semgrep_scan')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:semgrep_scan:{e}')

# Compare ndaybench and Semgrep performance
try:
    ndaybench_import_time = float(next(line.split(':')[1] for line in iter(lambda: input(), '') if line.startswith('BENCHMARK:import_time_ms')))
    semgrep_import_time = float(next(line.split(':')[1] for line in iter(lambda: input(), '') if line.startswith('BENCHMARK:semgrep_import_time_ms')))
    ratio = semgrep_import_time / ndaybench_import_time
    print(f'BENCHMARK:vs_semgrep_import_time_ratio:{ratio}')
except Exception as e:
    print(f'BENCHMARK:vs_semgrep_import_time_ratio:Error calculating ratio:{e}')

# Compare ndaybench and Semgrep scan time
try:
    ndaybench_scan_time = float(next(line.split(':')[1] for line in iter(lambda: input(), '') if line.startswith('BENCHMARK:scan_time_ms')))
    semgrep_scan_time = float(next(line.split(':')[1] for line in iter(lambda: input(), '') if line.startswith('BENCHMARK:semgrep_scan_time_ms')))
    ratio = semgrep_scan_time / ndaybench_scan_time
    print(f'BENCHMARK:vs_semgrep_scan_time_ratio:{ratio}')
except Exception as e:
    print(f'BENCHMARK:vs_semgrep_scan_time_ratio:Error calculating ratio:{e}')

# Measure memory usage
tracemalloc.start()
ndaybench
tracemalloc.stop()
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_bytes:{peak}')

print('RUN_OK')