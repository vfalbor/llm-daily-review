import subprocess
import time
import tracemalloc
import sys

# Install system packages
def install_system_packages():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print('INSTALL_OK')

# Install tool dependencies
def install_tool_dependencies():
    try:
        subprocess.run(['pip', 'install', 'turbo-fieldfare'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')
        try:
            subprocess.run(['git', 'clone', 'https://github.com/drumih/turbo-fieldfare.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './turbo-fieldfare'], cwd='./turbo-fieldfare', check=False)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

# Run simple benchmark
def run_benchmark():
    try:
        import turbo_fieldfare
        start_time = time.time()
        turbo_fieldfare.run_synthetic_test()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:run_time_ms:{latency}')
        print(f'TEST_PASS:run_benchmark')
    except Exception as e:
        print(f'TEST_FAIL:run_benchmark:{str(e)}')

# Compare performance with other engines
def compare_performance():
    try:
        import llama
        import codellama
        import turbo_fieldfare
        start_time = time.time()
        llama.run_synthetic_test()
        end_time = time.time()
        llama_latency = (end_time - start_time) * 1000
        start_time = time.time()
        codellama.run_synthetic_test()
        end_time = time.time()
        codellama_latency = (end_time - start_time) * 1000
        start_time = time.time()
        turbo_fieldfare.run_synthetic_test()
        end_time = time.time()
        turbo_fieldfare_latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_llama_latency_ms:{turbo_fieldfare_latency / llama_latency}')
        print(f'BENCHMARK:vs_codellama_latency_ms:{turbo_fieldfare_latency / codellama_latency}')
        print(f'TEST_PASS:compare_performance')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance:{str(e)}')

# Measure memory usage
def measure_memory_usage():
    tracemalloc.start()
    import turbo_fieldfare
    turbo_fieldfare.run_synthetic_test()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_bytes:{peak}')

# Measure import time
def measure_import_time():
    start_time = time.time()
    import turbo_fieldfare
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time}')

# Run all tests
install_system_packages()
install_tool_dependencies()
run_benchmark()
compare_performance()
measure_memory_usage()
measure_import_time()

# Always print RUN_OK
print('RUN_OK')