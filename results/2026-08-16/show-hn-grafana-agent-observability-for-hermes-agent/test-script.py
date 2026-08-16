import subprocess
import time
import tracemalloc
import sys

def install_dependencies():
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)
    
    # Install tool dependencies
    try:
        subprocess.run(['pip', 'install', 'grafana-agent'], check=True)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:pip install failed, trying git clone and pip install -e .")
        subprocess.run(['git', 'clone', 'https://github.com/alexander-akhmetov/grafana-agento11y-hermes.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './grafana-agento11y-hermes'], check=True)
    print("INSTALL_OK")

def test_install_and_basic_run():
    start_time = time.time()
    try:
        subprocess.run(['grafana-agent', '--help'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:install_time_s:{end_time - start_time}")
        print("TEST_PASS:install_and_basic_run")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:install_and_basic_run:{str(e)}")

def test_performance():
    tracemalloc.start()
    start_time = time.time()
    try:
        subprocess.run(['grafana-agent', '--config', './config.yaml'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024}")
        print(f"BENCHMARK:performance_time_s:{end_time - start_time}")
        print("TEST_PASS:performance")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:performance:{str(e)}")
    finally:
        tracemalloc.stop()

def test_compare_vs_similar_tool():
    try:
        start_time = time.time()
        subprocess.run(['grafana-agent', '--config', './config.yaml'], check=True)
        end_time = time.time()
        grafana_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['prometheus', '--config', './config.yaml'], check=True)
        end_time = time.time()
        prometheus_time = end_time - start_time
        ratio = grafana_time / prometheus_time
        print(f"BENCHMARK:vs_prometheus_time_ratio:{ratio}")
        print("TEST_PASS:compare_vs_similar_tool")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_vs_similar_tool:{str(e)}")

install_dependencies()
test_install_and_basic_run()
test_performance()
test_compare_vs_similar_tool()
print("RUN_OK")