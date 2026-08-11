import subprocess
import time
import tracemalloc
import sys

def install_dependency(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def install_pip_dependency(package):
    try:
        subprocess.run(['pip', 'install', package], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def install_git_dependency(repo):
    try:
        subprocess.run(['git', 'clone', repo], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def build_canario():
    try:
        subprocess.run(['cargo', 'build'], check=True)
        print('BUILD_OK')
    except Exception as e:
        print(f'BUILD_FAIL:{str(e)}')

def run_canario_test():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'test'], check=True)
        end_time = time.time()
        test_time = end_time - start_time
        print(f'BENCHMARK:canario_test_time_s:{test_time:.2f}')
        print('TEST_PASS:canario_test')
    except Exception as e:
        print(f'TEST_FAIL:canario_test:{str(e)}')

def measure_import_time():
    try:
        start_time = time.time()
        import canario
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:canario_import_time_ms:{import_time:.2f}')
        print('TEST_PASS:canario_import')
    except Exception as e:
        print(f'TEST_FAIL:canario_import:{str(e)}')

def measure_execution_time():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['cargo', 'run'], check=True)
        end_time = time.time()
        execution_time = end_time - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:canario_execution_time_s:{execution_time:.2f}')
        print(f'BENCHMARK:canario_peak_memory_mb:{peak / 10**6:.2f}')
        print('TEST_PASS:canario_execution')
    except Exception as e:
        print(f'TEST_FAIL:canario_execution:{str(e)}')

def compare_to_baseline():
    try:
        start_time = time.time()
        subprocess.run(['wezterm', '--help'], check=True)
        end_time = time.time()
        wezterm_time = end_time - start_time
        print(f'BENCHMARK:vs_wezterm_help_time_ratio:{wezterm_time / 0.1:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:wezterm_comparison:{str(e)}')

def main():
    install_dependency('git')
    install_git_dependency('https://github.com/raphalca/canario.git')
    install_dependency('cargo')
    build_canario()
    run_canario_test()
    measure_import_time()
    measure_execution_time()
    compare_to_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()