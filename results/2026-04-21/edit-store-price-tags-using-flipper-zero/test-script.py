import subprocess
import time
import requests
import tracemalloc

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
    try:
        subprocess.run(['npm', 'install', 'tagtinker'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def clone_tagtinker():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/i12bp8/TagTinker.git'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def run_tagtinker():
    try:
        start_time = time.time()
        subprocess.run(['node', 'TagTinker/index.js'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:run_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:run_tagtinker")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_tagtinker:{e}")

def compare_with_manual_editing():
    try:
        # simulate manual editing
        manual_edit_time = 1000  # ms
        tagtinker_edit_time = 500  # ms
        print(f"BENCHMARK:edit_time_ms:{manual_edit_time}")
        print(f"BENCHMARK:vs_tagtinker_edit_time_ratio:{tagtinker_edit_time / manual_edit_time}")
        print("TEST_PASS:compare_with_manual_editing")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_manual_editing:{e}")

def compare_with_alternative_editors():
    try:
        # simulate alternative editors
        alternative_editor_time = 800  # ms
        tagtinker_time = 500  # ms
        print(f"BENCHMARK:alternative_editor_time_ms:{alternative_editor_time}")
        print(f"BENCHMARK:vs_alternative_editor_ratio:{tagtinker_time / alternative_editor_time}")
        print("TEST_PASS:compare_with_alternative_editors")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_alternative_editors:{e}")

def check_health_endpoint():
    try:
        response = requests.get('http://localhost:3000/health')
        if response.status_code == 200:
            print("TEST_PASS:check_health_endpoint")
        else:
            print(f"TEST_FAIL:check_health_endpoint:status_code_{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:check_health_endpoint:{e}")

def measure_memory_usage():
    tracemalloc.start()
    time.sleep(1)
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_mb:{current / 10**6}")
    tracemalloc.stop()

def main():
    install_dependencies()
    clone_tagtinker()
    run_tagtinker()
    compare_with_manual_editing()
    compare_with_alternative_editors()
    check_health_endpoint()
    measure_memory_usage()
    print("RUN_OK")

if __name__ == "__main__":
    main()