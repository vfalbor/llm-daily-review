import subprocess
import time
import tracemalloc
import requests
from xml.etree import ElementTree
import os

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    try:
        subprocess.run(['pip', 'install', 'lineageos-stats'], check=True)
    except subprocess.CalledProcessError:
        print('INSTALL_FAIL:pip install failed, falling back to git clone + pip install -e .')
        subprocess.run(['git', 'clone', 'https://github.com/LineageOS/stats.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './stats'], cwd='./stats', check=True)

def test_visit_lineageos_stats_page():
    try:
        start_time = time.time()
        response = requests.get('https://stats.lineageos.org/')
        end_time = time.time()
        assert response.status_code == 200
        print('TEST_PASS:visit_lineageos_stats_page')
        print(f'BENCHMARK:visit_lineageos_stats_latenc_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:visit_lineageos_stats_page:{str(e)}')

def test_compare_lineageos_with_aosp():
    try:
        start_time = time.time()
        lineageos_response = requests.get('https://stats.lineageos.org/')
        aosp_response = requests.get('https://android.googlesource.com/')
        end_time = time.time()
        assert lineageos_response.status_code == 200
        assert aosp_response.status_code == 200
        lineageos_tree = ElementTree.fromstring(lineageos_response.content)
        aosp_tree = ElementTree.fromstring(aosp_response.content)
        # Basic comparison, actual comparison logic may vary based on requirement
        lineageos_stats = lineageos_tree.find('.//title').text
        aosp_stats = aosp_tree.find('.//title').text
        print('TEST_PASS:compare_lineageos_with_aosp')
        print(f'BENCHMARK:compare_lineageos_with_aosp_latenc_ms:{(end_time - start_time) * 1000}')
        # Compare trends and differences
        print(f'BENCHMARK:lineageos_stats:{len(lineageos_stats)}')
        print(f'BENCHMARK:aosp_stats:{len(aosp_stats)}')
        print(f'BENCHMARK:vs_aosp_stats_ratio:{len(lineageos_stats) / len(aosp_stats)}')
    except Exception as e:
        print(f'TEST_FAIL:compare_lineageos_with_aosp:{str(e)}')

def test_import_time():
    try:
        import lineageos_stats
        start_time = time.time()
        lineageos_stats.get_stats()
        end_time = time.time()
        print('TEST_PASS:import_time')
        print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:import_time:{str(e)}')

def benchmark_memory_usage():
    try:
        tracemalloc.start()
        import lineageos_stats
        start_time = time.time()
        lineageos_stats.get_stats()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_bytes:{current}')
        print(f'BENCHMARK:peak_memory_usage_bytes:{peak}')
        tracemalloc.stop()
    except Exception as e:
        print(f'TEST_FAIL:benchmark_memory_usage:{str(e)}')

def main():
    start_time = time.time()
    install_dependencies()
    end_time = time.time()
    print('INSTALL_OK')
    print(f'BENCHMARK:install_time_s:{end_time - start_time}')
    
    test_visit_lineageos_stats_page()
    test_compare_lineageos_with_aosp()
    test_import_time()
    benchmark_memory_usage()

    print('RUN_OK')

if __name__ == '__main__':
    main()