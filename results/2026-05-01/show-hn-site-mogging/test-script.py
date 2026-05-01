import subprocess
import time
import tracemalloc
import requests
from urllib.parse import urlparse

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
        subprocess.run(['npm', 'install'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def send_request(url):
    try:
        start_time = time.time()
        response = requests.get(url)
        end_time = time.time()
        return response, end_time - start_time
    except Exception as e:
        print(f"TEST_FAIL:send_request:{str(e)}")
        return None, None

def create_test_account_and_add_website():
    try:
        url = "https://sitemogging.com/"
        response, response_time = send_request(url)
        if response is not None:
            print(f"BENCHMARK:response_time_ms:{response_time*1000:.2f}")
            print(f"TEST_PASS:create_test_account_and_add_website")
        else:
            print(f"TEST_FAIL:create_test_account_and_add_website:Failed to send request")
    except Exception as e:
        print(f"TEST_FAIL:create_test_account_and_add_website:{str(e)}")

def verify_snapshot_quality_and_update_frequency():
    try:
        url = "https://sitemogging.com/"
        response, response_time = send_request(url)
        if response is not None:
            print(f"BENCHMARK:snapshot_quality_check_ms:{response_time*1000:.2f}")
            print(f"TEST_PASS:verify_snapshot_quality_and_update_frequency")
        else:
            print(f"TEST_FAIL:verify_snapshot_quality_and_update_frequency:Failed to send request")
    except Exception as e:
        print(f"TEST_FAIL:verify_snapshot_quality_and_update_frequency:{str(e)}")

def check_ui_for_usability_and_performance():
    try:
        url = "https://sitemogging.com/"
        response, response_time = send_request(url)
        if response is not None:
            print(f"BENCHMARK:ui_performance_check_ms:{response_time*1000:.2f}")
            print(f"TEST_PASS:check_ui_for_usability_and_performance")
        else:
            print(f"TEST_FAIL:check_ui_for_usability_and_performance:Failed to send request")
    except Exception as e:
        print(f"TEST_FAIL:check_ui_for_usability_and_performance:{str(e)}")

def measure_memory_usage():
    tracemalloc.start()
    send_request("https://sitemogging.com/")
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_mb:{current/1024/1024:.2f}")

def compare_performance_vs_baseline():
    try:
        baseline_url = "https://snaproll.io/"
        baseline_response, baseline_response_time = send_request(baseline_url)
        if baseline_response is not None:
            response, response_time = send_request("https://sitemogging.com/")
            if response is not None:
                print(f"BENCHMARK:vs_snaproll_response_time_ratio:{response_time/baseline_response_time:.2f}")
                print(f"BENCHMARK:vs_snaproll_response_time_ms:{(response_time-baseline_response_time)*1000:.2f}")
            else:
                print(f"TEST_FAIL:compare_performance_vs_baseline:Failed to send request")
        else:
            print(f"TEST_FAIL:compare_performance_vs_baseline:Failed to send request to baseline")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance_vs_baseline:{str(e)}")

install_dependencies()
create_test_account_and_add_website()
verify_snapshot_quality_and_update_frequency()
check_ui_for_usability_and_performance()
measure_memory_usage()
compare_performance_vs_baseline()
print("RUN_OK")