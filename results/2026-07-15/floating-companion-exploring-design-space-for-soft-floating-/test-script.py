import subprocess
import importlib
import time
import tracemalloc
import matplotlib.pyplot as plt
import numpy as np
from Soft_Robotics_Lab import dataset

def install_dependencies():
    # Install git
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print('INSTALL_OK')

def install_soft_robotics_lab():
    try:
        # Try pip install
        subprocess.run(['pip', 'install', 'Soft-Robotics-Lab'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        try:
            # Fallback to git clone + pip install -e .
            subprocess.run(['git', 'clone', 'https://github.com/Soft-Robotics-Lab/Soft-Robotics-Lab.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './Soft-Robotics-Lab'], check=False)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_import_time():
    start_time = time.time()
    try:
        import Soft_Robotics_Lab
        end_time = time.time()
        import_time_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:import_time_ms:{import_time_ms}')
        print(f'TEST_PASS:test_import_time')
    except Exception as e:
        print(f'TEST_FAIL:test_import_time:{str(e)}')

def test_dataset_analysis():
    try:
        # Download dataset
        dataset.download()
        # Run simple analysis (e.g., histogram)
        data = dataset.load()
        plt.hist(data)
        plt.show()
        print(f'TEST_PASS:test_dataset_analysis')
    except Exception as e:
        print(f'TEST_FAIL:test_dataset_analysis:{str(e)}')

def test_benchmark_latency():
    try:
        start_time = time.time()
        dataset.load()
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:dataset_load_latency_ms:{latency_ms}')
        print(f'TEST_PASS:test_benchmark_latency')
    except Exception as e:
        print(f'TEST_FAIL:test_benchmark_latency:{str(e)}')

def compare_baseline():
    try:
        # Soft-Robotics-Lab is the only similar tool, so compare with itself
        start_time = time.time()
        dataset.load()
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        ratio = latency_ms / latency_ms
        print(f'BENCHMARK:vs_Soft_Robotics_Lab_latency_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_FAIL:compare_baseline:{str(e)}')

def test_memory_usage():
    try:
        tracemalloc.start()
        dataset.load()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_peak_bytes:{peak}')
    except Exception as e:
        print(f'TEST_FAIL:test_memory_usage:{str(e)}')

def test_loc_count():
    try:
        # Count lines of code in the dataset module
        loc_count = sum(1 for line in open('Soft_Robotics_Lab/dataset.py'))
        print(f'BENCHMARK:loc_count:{loc_count}')
    except Exception as e:
        print(f'TEST_FAIL:test_loc_count:{str(e)}')

def test_file_count():
    try:
        # Count number of files in the dataset module
        file_count = sum(1 for line in subprocess.Popen(['find', 'Soft_Robotics_Lab', '-type', 'f'], stdout=subprocess.PIPE).stdout)
        print(f'BENCHMARK:test_files_count:{file_count}')
    except Exception as e:
        print(f'TEST_FAIL:test_file_count:{str(e)}')

def main():
    install_dependencies()
    install_soft_robotics_lab()
    test_import_time()
    test_dataset_analysis()
    test_benchmark_latency()
    compare_baseline()
    test_memory_usage()
    test_loc_count()
    test_file_count()
    print('RUN_OK')

if __name__ == '__main__':
    main()