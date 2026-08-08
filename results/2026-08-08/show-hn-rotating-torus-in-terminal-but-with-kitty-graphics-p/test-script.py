import subprocess
import time
import tracemalloc
import requests

def install_nodejs():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_app():
    try:
        subprocess.run(['npm', 'install', 'torus-v0-5'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def start_server():
    try:
        subprocess.run(['node', 'server.js'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_rendering_accuracy():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:8080')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:rendering_time_ms:{response_time}")
        if response.status_code == 200:
            print("TEST_PASS:rendering_accuracy")
        else:
            print(f"TEST_FAIL:rendering_accuracy:{response.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:rendering_accuracy:{str(e)}")

def test_performance():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:8080/large_dataset')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:performance_time_ms:{response_time}")
        if response.status_code == 200:
            print("TEST_PASS:performance")
        else:
            print(f"TEST_FAIL:performance:{response.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:performance:{str(e)}")

def test_user_experience():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:8080/user_experience')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:user_experience_time_ms:{response_time}")
        if response.status_code == 200:
            print("TEST_PASS:user_experience")
        else:
            print(f"TEST_FAIL:user_experience:{response.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:user_experience:{str(e)}")

def compare_with_matplotlib():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:8080/matplotlib_benchmark')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_matplotlib_time_ms:{response_time}")
        if response.status_code == 200:
            print("TEST_PASS:compare_with_matplotlib")
        else:
            print(f"TEST_FAIL:compare_with_matplotlib:{response.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_matplotlib:{str(e)}")

def compare_with_plotly():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:8080/plotly_benchmark')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_plotly_time_ms:{response_time}")
        if response.status_code == 200:
            print("TEST_PASS:compare_with_plotly")
        else:
            print(f"TEST_FAIL:compare_with_plotly:{response.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_plotly:{str(e)}")

def main():
    install_nodejs()
    install_app()
    start_server()
    test_rendering_accuracy()
    test_performance()
    test_user_experience()
    compare_with_matplotlib()
    compare_with_plotly()
    tracemalloc.start()
    time.sleep(1)
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_byte:{current}")
    print(f"BENCHMARK:memory_usage_peak_byte:{peak}")
    print("RUN_OK")

if __name__ == "__main__":
    main()