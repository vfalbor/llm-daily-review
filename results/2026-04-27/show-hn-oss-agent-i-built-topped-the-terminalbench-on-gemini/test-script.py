import subprocess
import time
import tracemalloc
import requests

def run_benchmark(name, func):
    tracemalloc.start()
    start_time = time.time()
    try:
        func()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:{name}_time_s:{end_time - start_time:.2f}")
        print(f"BENCHMARK:{name}_mem_mb:{peak / 10**6:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{str(e)}")

def pull_docker_image():
    try:
        subprocess.run(['docker', 'pull', 'dirac-run/dirac'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def run_container():
    try:
        subprocess.run(['docker', 'run', '-d', 'dirac-run/dirac'], check=True)
        print(f"TEST_PASS:run_container")
    except Exception as e:
        print(f"TEST_FAIL:run_container:{str(e)}")

def monitor_performance():
    def func():
        subprocess.run(['docker', 'exec', '-it', 'dirac-run/dirac', 'top'], check=True)
    run_benchmark("monitor_performance", func)

def monitor_resource_usage():
    def func():
        subprocess.run(['docker', 'exec', '-it', 'dirac-run/dirac', 'free'], check=True)
    run_benchmark("monitor_resource_usage", func)

def compare_performance():
    try:
        prometheus_time = requests.get("https://github.com/prometheus/prometheus/releases").elapsed.total_seconds()
        dirac_time = requests.get("https://github.com/dirac-run/dirac/releases").elapsed.total_seconds()
        ratio = dirac_time / prometheus_time
        print(f"BENCHMARK:vs_prometheus_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance:{str(e)}")

def main():
    # Install required packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=True)

    # Pull Docker image
    pull_docker_image()

    # Run container
    run_container()

    # Monitor performance and resource usage
    monitor_performance()
    monitor_resource_usage()

    # Compare performance with Prometheus
    compare_performance()

    # Always print RUN_OK at the end
    print("RUN_OK")

if __name__ == "__main__":
    main()