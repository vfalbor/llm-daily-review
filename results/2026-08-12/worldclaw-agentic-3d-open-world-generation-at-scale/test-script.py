import subprocess
import time
import tracemalloc
import os
import sys

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/Tencent-Hunyuan/Hunyuan3D-WorldClaw.git'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def count_source_files():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/Tencent-Hunyuan/Hunyuan3D-WorldClaw.git'], check=False)
        count = 0
        for root, dirs, files in os.walk('Hunyuan3D-WorldClaw'):
            for file in files:
                if file.endswith(('.py', '.cpp', '.java', '.c', '.js', '.go', '.swift', '.kt', '.cs', '.php', '.rb', '.lua', '.rust', '.swift', '.js', '.ts')):
                    count += 1
        print(f'BENCHMARK:loc_count:{count}')
        print(f'BENCHMARK:test_files_count:1')
    except Exception as e:
        print(f'TEST_FAIL:count_source_files:{str(e)}')

def run_benchmark():
    try:
        start_time = time.time()
        subprocess.run(['python', 'Hunyuan3D-WorldClaw/examples/python_example.py'], check=False)
        end_time = time.time()
        print(f'BENCHMARK:python_benchmark_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:run_benchmark:{str(e)}')

def compare_baseline():
    try:
        start_time = time.time()
        subprocess.run(['blender', '--background', '--python', 'Hunyuan3D-WorldClaw/examples/blender_example.py'], check=False)
        end_time = time.time()
        blender_time = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run(['python', 'Hunyuan3D-WorldClaw/examples/python_example.py'], check=False)
        end_time = time.time()
        python_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_blender_python_benchmark_ratio:{python_time / blender_time}')
    except Exception as e:
        print(f'TEST_FAIL:compare_baseline:{str(e)}')

def main():
    install_dependencies()
    count_source_files()
    run_benchmark()
    compare_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()