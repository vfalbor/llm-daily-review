import subprocess
import time
import tracemalloc
import requests

def install_apk_package(pkg_name):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg_name], check=True)
        print(f"INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install {pkg_name}, error code {e.returncode}")

def install_pip_package(pkg_name):
    try:
        subprocess.run(['pip', 'install', pkg_name], check=True)
        print(f"INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install {pkg_name}, error code {e.returncode}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/umami-so/umami.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './umami'], check=True)
            print(f"INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:Failed to install {pkg_name} from source, error code {e.returncode}")

def test_umami_instance():
    try:
        start_time = time.time()
        subprocess.run(['umami', '--help'], check=True)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:umami_cli_time_ms:{execution_time:.2f}")
        print(f"TEST_PASS:umami_instance")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:umami_instance:Error code {e.returncode}")

def test_ios_app_analytics_integration():
    try:
        start_time = time.time()
        subprocess.run(['curl', '-X', 'POST', 'https://example.com/umami/api/track'], check=True)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:ios_app_analytics_time_ms:{execution_time:.2f}")
        print(f"TEST_PASS:ios_app_analytics_integration")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:ios_app_analytics_integration:Error code {e.returncode}")

def test_data_collection_and_analytics_correctness():
    try:
        start_time = time.time()
        response = requests.get('https://example.com/umami/api/events')
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:data_collection_time_ms:{execution_time:.2f}")
        if response.status_code == 200:
            print(f"TEST_PASS:data_collection_and_analytics_correctness")
        else:
            print(f"TEST_FAIL:data_collection_and_analytics_correctness:Status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:data_collection_and_analytics_correctness:Error {e}")

def compare_performance_with_baseline():
    try:
        start_time = time.time()
        subprocess.run(['amplitude', '--help'], check=True)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:amplitude_cli_time_ms:{execution_time:.2f}")
        umami_time = float(next((line.split(":")[1] for line in output.splitlines() if line.startswith("BENCHMARK:umami_cli_time_ms")), None))
        amplitude_time = float(next((line.split(":")[1] for line in output.splitlines() if line.startswith("BENCHMARK:amplitude_cli_time_ms")), None))
        ratio = umami_time / amplitude_time
        print(f"BENCHMARK:vs_amplitude_cli_time_ratio:{ratio:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_performance_with_baseline:Error code {e.returncode}")

def main():
    global output
    tracemalloc.start()
    install_apk_package('git')
    install_apk_package('curl')
    install_pip_package('umami')
    test_umami_instance()
    test_ios_app_analytics_integration()
    test_data_collection_and_analytics_correctness()
    compare_performance_with_baseline()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_peak_bytes:{peak}")
    print(f"BENCHMARK:memory_usage_current_bytes:{current}")
    tracemalloc.stop()
    print(f"RUN_OK")

if __name__ == "__main__":
    main()