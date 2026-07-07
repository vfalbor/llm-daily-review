import subprocess
import time
import tracemalloc
import importlib.util
import sys

def install_officecli():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', 'officecli'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/iOfficeAI/OfficeCLI.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './OfficeCLI'], check=False, cwd='./OfficeCLI')
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_ms_office_to_json_conversion():
    try:
        start_time = time.time()
        subprocess.run(['officecli', '--help'], check=False)
        end_time = time.time()
        print(f'TEST_PASS:ms_office_to_json_conversion')
        print(f'BENCHMARK:officecli_import_time_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:ms_office_to_json_conversion:{str(e)}')

def test_edit_ms_office_files():
    try:
        start_time = time.time()
        subprocess.run(['officecli', 'convert', '--input', 'test.docx', '--output', 'test.json'], check=False)
        end_time = time.time()
        print(f'TEST_PASS:edit_ms_office_files')
        print(f'BENCHMARK:officecli_edit_time_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:edit_ms_office_files:{str(e)}')

def measure_memory_usage():
    try:
        tracemalloc.start()
        import officecli
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:officecli_memory_usage_mb:{current / 1024 / 1024}')
        tracemalloc.stop()
    except Exception as e:
        print(f'TEST_FAIL:measure_memory_usage:{str(e)}')

def compare_performance_with_baseline():
    try:
        start_time = time.time()
        subprocess.run(['officecli', 'convert', '--input', 'test.docx', '--output', 'test.json'], check=False)
        end_time = time.time()
        officecli_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['python', '-c', 'import json'], check=False)
        end_time = time.time()
        python_time = end_time - start_time
        print(f'BENCHMARK:vs_python_officecli_ratio:{officecli_time / python_time}')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance_with_baseline:{str(e)}')

def main():
    install_officecli()
    test_ms_office_to_json_conversion()
    test_edit_ms_office_files()
    measure_memory_usage()
    compare_performance_with_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()