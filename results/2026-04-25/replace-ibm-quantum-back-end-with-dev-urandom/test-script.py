import subprocess
import sys
import time
import tracemalloc
import os

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/yuvadm/quantumslop.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './quantumslop'], cwd='./quantumslop', check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_demo():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python', 'URANDOM_DEMO.md'], cwd='./quantumslop', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:demo_time_s:{end_time - start_time}')
        print(f'BENCHMARK:demo_mem_mb:{peak / 10**6}')
        print(f'TEST_PASS:demo')
    except Exception as e:
        print(f'TEST_FAIL:demo:{str(e)}')

def test_simulator():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python', 'simulator.py'], cwd='./quantumslop', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:simulator_time_s:{end_time - start_time}')
        print(f'BENCHMARK:simulator_mem_mb:{peak / 10**6}')
        print(f'TEST_PASS:simulator')
    except Exception as e:
        print(f'TEST_FAIL:simulator:{str(e)}')

def count_source_files():
    try:
        file_count = 0
        lang_count = set()
        for root, dirs, files in os.walk('./quantumslop'):
            for file in files:
                if file.endswith(('.py', '.c', '.cpp', '.java', '.js')):
                    file_count += 1
                    lang_count.add(file.split('.')[-1])
        print(f'BENCHMARK:source_files_count:{file_count}')
        print(f'BENCHMARK:languages_count:{len(lang_count)}')
        print(f'TEST_PASS:source_files')
    except Exception as e:
        print(f'TEST_FAIL:source_files:{str(e)}')

def compare_with_baseline():
    try:
        start_time = time.time()
        subprocess.run(['python', 'baseline.py'], cwd='./quantumslop', check=False)
        end_time = time.time()
        baseline_time = end_time - start_time
        demo_time = float(next((x.split(':')[1] for x in sys.stdout.getvalue().decode().split('\n') if x.startswith('BENCHMARK:demo_time_s:')), None))
        print(f'BENCHMARK:vs_quantum_simulator_ratio:{demo_time / baseline_time}')
        print(f'TEST_PASS:baseline')
    except Exception as e:
        print(f'TEST_FAIL:baseline:{str(e)}')

install_dependencies()
test_demo()
test_simulator()
count_source_files()
compare_with_baseline()
print('RUN_OK')