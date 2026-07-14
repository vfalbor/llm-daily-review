import subprocess
import time
import tracemalloc
import json
import requests

def run_command(command):
    try:
        subprocess.run(command, check=True)
        return "INSTALL_OK"
    except subprocess.CalledProcessError as e:
        return f"INSTALL_FAIL:{str(e)}"

def test_installation():
    print(run_command(['apk', 'add', '--no-cache', 'git', 'curl']))
    print(run_command(['npm', 'install', '-g', 'satellitemap']))
    return "TEST_PASS:install" if subprocess.run(['which', 'satellitemap'], check=False).returncode == 0 else "TEST_FAIL:install:command not found"

def test_visualize_satellites():
    try:
        start_time = time.time()
        subprocess.run(['satellitemap', 'visualize'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:visualize_satellites_s:{end_time - start_time}")
        return "TEST_PASS:visualize_satellites"
    except subprocess.CalledProcessError as e:
        return f"TEST_FAIL:visualize_satellites:{str(e)}"

def test_add_new_satellite():
    try:
        start_time = time.time()
        subprocess.run(['satellitemap', 'add', 'new_satellite'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:add_satellite_s:{end_time - start_time}")
        return "TEST_PASS:add_new_satellite"
    except subprocess.CalledProcessError as e:
        return f"TEST_FAIL:add_new_satellite:{str(e)}"

def test_optimize_map_loading():
    try:
        start_time = time.time()
        subprocess.run(['satellitemap', 'optimize'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:optimize_map_loading_s:{end_time - start_time}")
        return "TEST_PASS:optimize_map_loading"
    except subprocess.CalledProcessError as e:
        return f"TEST_FAIL:optimize_map_loading:{str(e)}"

def test_measure_fps():
    try:
        start_time = time.time()
        subprocess.run(['satellitemap', 'measure', 'fps'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:measure_fps_s:{end_time - start_time}")
        return "TEST_PASS:measure_fps"
    except subprocess.CalledProcessError as e:
        return f"TEST_FAIL:measure_fps:{str(e)}"

def compare_performance():
    try:
        # Get the performance metrics of the baseline tool
        baseline_tool = 'Starlink Status'
        baseline_metrics = requests.get(f'https://api.example.com/metrics/{baseline_tool}').json()
        # Get the performance metrics of the current tool
        current_metrics = requests.get('https://api.example.com/metrics/satellitemap').json()
        # Calculate the ratio of the current tool's performance to the baseline tool's performance
        ratio = current_metrics['fps'] / baseline_metrics['fps']
        print(f"BENCHMARK:vs_starlink_status_fps_ratio:{ratio}")
        return "TEST_PASS:compare_performance"
    except requests.exceptions.RequestException as e:
        return f"TEST_FAIL:compare_performance:{str(e)}"

def main():
    print(run_command(['apk', 'add', '--no-cache', 'git', 'curl']))
    print(run_command(['npm', 'install', '-g', 'satellitemap']))
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['npm', 'install', '-g', 'satellitemap'], check=False)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:install_time_s:{time.time() - start_time}")
    print(f"BENCHMARK:install_memory_mb:{current / 1024 / 1024}")
    print(test_installation())
    print(test_visualize_satellites())
    print(test_add_new_satellite())
    print(test_optimize_map_loading())
    print(test_measure_fps())
    print(compare_performance())
    print("RUN_OK")

if __name__ == "__main__":
    main()