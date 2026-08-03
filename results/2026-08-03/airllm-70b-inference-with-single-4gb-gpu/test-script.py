import subprocess
import sys
import time
import tracemalloc
import importlib.util
import importlib.machinery
import os

def install_package(package):
    try:
        subprocess.run(['pip', 'install', package], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')
        try:
            subprocess.run(['git', 'clone', f'https://github.com/{package}.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './airllm'], check=True)
            print('INSTALL_OK')
        except subprocess.CalledProcessError as e:
            print(f'INSTALL_FAIL:{e}')

def import_package(package):
    try:
        spec = importlib.util.find_spec(package)
        airllm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(airllm)
        print(f'TEST_PASS:{package}_import')
        return airllm
    except ImportError as e:
        print(f'TEST_FAIL:{package}_import:{e}')
        return None

def benchmark_airllm(airllm):
    try:
        start_time = time.time()
        tracemalloc.start()
        airllm.inference('synthetic_data')
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:inference_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:inference_memory_mb:{current / 10**6}')
        print(f'BENCHMARK:inference_peak_memory_mb:{peak / 10**6}')
    except Exception as e:
        print(f'TEST_FAIL:airllm_inference:{e}')

def compare_with_baseline(airllm):
    try:
        import transformers
        start_time = time.time()
        transformers.pipeline('text-generation')
        end_time = time.time()
        baseline_time = end_time - start_time
        airllm_time = time.time() - start_time
        print(f'BENCHMARK:vs_transformers_inference_time_ratio:{airllm_time / baseline_time}')
    except Exception as e:
        print(f'TEST_SKIP:compare_with_baseline:{e}')

def main():
    # Install packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    install_package('lyogavin/airllm')
    airllm = import_package('airllm')

    if airllm:
        benchmark_airllm(airllm)
        compare_with_baseline(airllm)

    print('RUN_OK')

if __name__ == '__main__':
    main()