import subprocess
import sys
import time
import tracemalloc
import requests

def install_package(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False)
        print(f"INSTALL_OK: {pkg}")
    except Exception as e:
        print(f"INSTALL_FAIL: {pkg} - {str(e)}")

def install_tool_dependencies(tool, method='pip'):
    try:
        if method == 'pip':
            subprocess.run(['pip', 'install', tool], check=False)
        elif method == 'git':
            subprocess.run(['git', 'clone', f'https://github.com/{tool}.git'], check=False)
            subprocess.run(['pip', 'install', '-e', f'./{tool}'], check=False)
        print(f"INSTALL_OK: {tool}")
    except Exception as e:
        print(f"INSTALL_FAIL: {tool} - {str(e)}")

def run_workload():
    try:
        start_time = time.time()
        # Mock API call with fake key
        response = requests.get('https://mock-api.com', headers={'Authorization': 'Bearer fake-key'})
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code}")
        end_time = time.time()
        workload_time = end_time - start_time
        print(f"BENCHMARK:workload_time_ms:{workload_time*1000:.2f}")
        return workload_time
    except Exception as e:
        print(f"TEST_FAIL:run_workload - {str(e)}")
        return None

def compare_performance(baseline_tool, workload_time):
    try:
        # Mock API call with fake key to get baseline tool performance
        response = requests.get(f'https://mock-api.com/{baseline_tool}', headers={'Authorization': 'Bearer fake-key'})
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code}")
        baseline_time = float(response.json()['time'])
        ratio = workload_time / baseline_time
        print(f"BENCHMARK:vs_{baseline_tool}_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance - {str(e)}")

def main():
    install_package('git')
    install_package('curl')
    install_tool_dependencies('cerebras', method='git')

    workload_time = run_workload()
    if workload_time is not None:
        compare_performance('nvidia_v100', workload_time)

    # Measure import time
    start_time = time.time()
    import cerebras
    end_time = time.time()
    import_time = end_time - start_time
    print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")

    # Measure memory usage
    tracemalloc.start()
    import cerebras
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_mb:{peak/1024/1024:.2f}")

    # Measure LOC count
    subprocess.run(['git', 'clone', 'https://github.com/cerebras/cerebras.git'], check=False)
    loc_count = subprocess.run(['wc', '-l', './cerebras/**/*.py'], check=False, stdout=subprocess.PIPE).stdout.decode().strip()
    print(f"BENCHMARK:loc_count:{loc_count}")

    print("RUN_OK")

if __name__ == "__main__":
    main()