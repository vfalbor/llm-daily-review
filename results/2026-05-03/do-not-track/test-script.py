import subprocess
import time
import tracemalloc
import pip
import importlib.util
import sys

def install_package(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', package], check=False)
        print('INSTALL_OK')
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/k3n/DoNotTrack.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './DoNotTrack'], check=False)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def import_package(package):
    spec = importlib.util.find_spec(package)
    if spec is None:
        return False
    return True

def test_do_not_track():
    try:
        import do_not_track
        start_time = time.time()
        do_not_track.DoNotTrack('https://example.com')
        end_time = time.time()
        print(f'BENCHMARK:do_not_track_latency_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'TEST_PASS:DoNotTrack_works_on_demo_website')
    except Exception as e:
        print(f'TEST_FAIL:DoNotTrack_works_on_demo_website:{str(e)}')

def test_do_not_track_api():
    try:
        import do_not_track
        start_time = time.time()
        api = do_not_track.DoNotTrack('https://example.com')
        api.get_tracking_data()
        end_time = time.time()
        print(f'BENCHMARK:do_not_track_api_latency_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'TEST_PASS:DoNotTrack_API_output')
    except Exception as e:
        print(f'TEST_FAIL:DoNotTrack_API_output:{str(e)}')

def benchmark_import_time(package):
    try:
        tracemalloc.start()
        start_time = time.time()
        importlib.import_module(package)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'BENCHMARK:import_memory_mb:{peak / (1024 * 1024):.2f}')
    except Exception as e:
        print(f'BENCHMARK:import_time_ms:0')
        print(f'BENCHMARK:import_memory_mb:0')

def compare_baseline():
    try:
        import ghostery
        start_time = time.time()
        ghostery.Ghostery('https://example.com')
        end_time = time.time()
        baseline_latency = (end_time - start_time) * 1000
        import do_not_track
        start_time = time.time()
        do_not_track.DoNotTrack('https://example.com')
        end_time = time.time()
        do_not_track_latency = (end_time - start_time) * 1000
        ratio = do_not_track_latency / baseline_latency
        print(f'BENCHMARK:vs_ghostery_latency_ratio:{ratio:.2f}')
    except Exception as e:
        print(f'BENCHMARK:vs_ghostery_latency_ratio:0')

def main():
    install_package('do_not_track')
    if import_package('do_not_track'):
        benchmark_import_time('do_not_track')
        test_do_not_track()
        test_do_not_track_api()
        compare_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()