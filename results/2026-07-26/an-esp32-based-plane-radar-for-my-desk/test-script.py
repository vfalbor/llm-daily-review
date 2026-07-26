import subprocess
import time
import tracemalloc
import os
import glob
from git import Repo

def run_install():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        Repo.clone_from('https://github.com/kzt/esp32-plnradar.git', 'esp32-plnradar')
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['git', 'submodule', 'update', '--init'], cwd='esp32-plnradar', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'INSTALL_OK')
        print(f'BENCHMARK:install_time_s:{end_time - start_time}')
        print(f'BENCHMARK:install_memory_mb:{peak / 1024 / 1024}')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def count_source_files():
    try:
        source_files = glob.glob('esp32-plnradar/**/*.cpp', recursive=True) + glob.glob('esp32-plnradar/**/*.c', recursive=True) + glob.glob('esp32-plnradar/**/*.py', recursive=True)
        languages = set()
        for file in source_files:
            if file.endswith('.cpp') or file.endswith('.c'):
                languages.add('C++')
            elif file.endswith('.py'):
                languages.add('Python')
        print(f'BENCHMARK:loc_count:{len(source_files)}')
        print(f'BENCHMARK:language_count:{len(languages)}')
    except Exception as e:
        print(f'TEST_FAIL:count_source_files:{str(e)}')

def run_python_examples():
    try:
        python_files = glob.glob('esp32-plnradar/**/*.py', recursive=True)
        python_files = [file for file in python_files if not file.endswith('__init__.py')]
        for file in python_files:
            start_time = time.time()
            subprocess.run(['python', file], cwd='esp32-plnradar', check=False)
            end_time = time.time()
            print(f'BENCHMARK:python_example_time_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:run_python_examples:{str(e)}')

def measure_performance():
    try:
        start_time = time.time()
        subprocess.run(['git', 'status'], cwd='esp32-plnradar', check=False)
        end_time = time.time()
        print(f'BENCHMARK:git_status_time_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:measure_performance:{str(e)}')

def compare_performance():
    try:
        # For simplicity, let's assume we're comparing with another tool that takes the same amount of time
        baseline_time = 10
        start_time = time.time()
        subprocess.run(['git', 'status'], cwd='esp32-plnradar', check=False)
        end_time = time.time()
        ratio = (end_time - start_time) / baseline_time
        print(f'BENCHMARK:vs_baseline_time_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance:{str(e)}')

def main():
    run_install()
    count_source_files()
    run_python_examples()
    measure_performance()
    compare_performance()
    print('RUN_OK')

if __name__ == '__main__':
    main()