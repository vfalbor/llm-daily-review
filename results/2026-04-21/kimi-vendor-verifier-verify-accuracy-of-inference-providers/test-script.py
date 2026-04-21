import subprocess
import time
import tracemalloc
import importlib
import sys

# Install git package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK' if subprocess.run(['which', 'git'], check=False).returncode == 0 else 'INSTALL_FAIL:git installation failed')

# Install tool dependencies
try:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'kimivendor-verifier'])
    print('INSTALL_OK')
except subprocess.CalledProcessError:
    try:
        subprocess.check_call(['git', 'clone', 'https://github.com/kimi-innovation/kimivendor-verifier'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', './kimivendor-verifier'])
        print('INSTALL_OK')
    except subprocess.CalledProcessError:
        print('INSTALL_FAIL:tool installation failed')
        print('RUN_OK')
        sys.exit(1)

# Measure import time
import_time_start = time.time()
try:
    import kimivendor_verifier
    import_time_end = time.time()
    print(f'BENCHMARK:import_time_ms:{int((import_time_end - import_time_start) * 1000)}')
except ImportError as e:
    print(f'TEST_FAIL:import_test:{str(e)}')

# Measure simple test performance
test_time_start = time.time()
try:
    kimivendor_verifier.verify_synthetic_data()
    test_time_end = time.time()
    print(f'BENCHMARK:simple_test_ms:{int((test_time_end - test_time_start) * 1000)}')
    print('TEST_PASS:simple_test')
except Exception as e:
    print(f'TEST_FAIL:simple_test:{str(e)}')

# Measure memory usage
tracemalloc.start()
try:
    kimivendor_verifier.verify_synthetic_data()
finally:
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}')
    print(f'BENCHMARK:peak_memory_usage_mb:{peak / (1024 * 1024)}')

# Baseline comparison with Semgrep
try:
    import semgrep
    baseline_time_start = time.time()
    semgrep.run(['--config', 'auto'])
    baseline_time_end = time.time()
    baseline_time = baseline_time_end - baseline_time_start
    our_time_start = time.time()
    kimivendor_verifier.verify_synthetic_data()
    our_time_end = time.time()
    our_time = our_time_end - our_time_start
    ratio = our_time / baseline_time
    print(f'BENCHMARK:vs_semgrep_ratio:{ratio}')
except ImportError:
    print('TEST_SKIP:baseline_comparison:no Semgrep installation found')

print('RUN_OK')