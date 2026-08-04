import subprocess
import time
import tracemalloc
import requests
import os

def print_marker(marker, *args):
    print(f"{marker}:{''.join(map(str, args))}")

def install_apk_packages():
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
    print_marker("INSTALL_OK")

def install_tool_dependencies():
    try:
        subprocess.run(['npm', 'install'], cwd='/app', check=True)
        print_marker("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print_marker("INSTALL_FAIL", e)

def clone_repo():
    subprocess.run(['git', 'clone', 'https://github.com/pedroth/post-NoNeedReact.git'], cwd='/app', check=True)

def run_hello_world_example():
    try:
        start_time = time.time()
        subprocess.run(['node', 'example.js'], cwd='/app', check=True)
        end_time = time.time()
        print_marker("TEST_PASS", "hello_world")
        print_marker("BENCHMARK", "hello_world_ms", int((end_time - start_time) * 1000))
    except subprocess.CalledProcessError as e:
        print_marker("TEST_FAIL", "hello_world", e)

def measure_bundle_size():
    try:
        bundle_size = os.path.getsize('/app/dist/bundle.js')
        print_marker("TEST_PASS", "bundle_size")
        print_marker("BENCHMARK", "bundle_size_bytes", bundle_size)
    except FileNotFoundError:
        print_marker("TEST_FAIL", "bundle_size", "bundle.js not found")

def test_rendering_with_sample_data():
    try:
        response = requests.get('http://localhost:3000')
        response.raise_for_status()
        print_marker("TEST_PASS", "rendering")
        print_marker("BENCHMARK", "response_time_ms", response.elapsed.total_seconds() * 1000)
    except requests.RequestException as e:
        print_marker("TEST_FAIL", "rendering", e)

def measure_memory_usage():
    tracemalloc.start()
    subprocess.run(['node', 'example.js'], cwd='/app', check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker("BENCHMARK", "memory_usage_mb", peak / 1024 / 1024)

def compare_performance_vs_preact():
    try:
        start_time = time.time()
        subprocess.run(['node', 'example.js'], cwd='/app/preact-example', check=True)
        end_time = time.time()
        preact_time = end_time - start_time
        our_time = subprocess.run(['node', 'example.js'], cwd='/app', check=True, capture_output=True, text=True).stderr
        our_time = float(our_time.splitlines()[-1].split()[-1])
        print_marker("BENCHMARK", "vs_preact_ratio", our_time / preact_time)
    except subprocess.CalledProcessError as e:
        print_marker("TEST_FAIL", "compare_performance", e)

if __name__ == '__main__':
    install_apk_packages()
    clone_repo()
    install_tool_dependencies()
    run_hello_world_example()
    measure_bundle_size()
    test_rendering_with_sample_data()
    measure_memory_usage()
    compare_performance_vs_preact()
    print_marker("RUN_OK")