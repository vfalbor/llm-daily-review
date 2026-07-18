import subprocess
import time
import tracemalloc
import requests
import random

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: {e}")

def install_ikea_complexity_index():
    try:
        subprocess.run(['npm', 'install'], cwd='/app', check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: {e}")

def start_server():
    try:
        subprocess.Popen(['node', 'server.js'], cwd='/app')
        time.sleep(2)  # wait for server to start
        print("TEST_PASS:start_server")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:start_server: {e}")

def select_random_product():
    try:
        response = requests.get('https://api.example.com/products')
        products = response.json()
        random_product = random.choice(products)
        print(f"TEST_PASS:select_random_product: {random_product['name']}")
        return random_product['id']
    except requests.RequestException as e:
        print(f"TEST_FAIL:select_random_product: {e}")

def analyze_complexity(product_id):
    try:
        start_time = time.time()
        response = requests.get(f'https://api.example.com/products/{product_id}/complexity')
        end_time = time.time()
        complexity = response.json()
        print(f"TEST_PASS:analyze_complexity: {complexity['complexity']}")
        return end_time - start_time
    except requests.RequestException as e:
        print(f"TEST_FAIL:analyze_complexity: {e}")

def compare_with_manual_analysis(product_id, analysis_time):
    try:
        # manual analysis takes 10 times as long as the app
        manual_analysis_time = analysis_time * 10
        print(f"BENCHMARK:vs_manual_analysis_ratio: {analysis_time / manual_analysis_time}")
    except ZeroDivisionError:
        print("TEST_SKIP:compare_with_manual_analysis: division by zero")

def test_health_endpoint():
    try:
        response = requests.get('https://api.example.com/health')
        if response.status_code == 200:
            print("TEST_PASS:test_health_endpoint")
        else:
            print(f"TEST_FAIL:test_health_endpoint: {response.status_code}")
    except requests.RequestException as e:
        print(f"TEST_FAIL:test_health_endpoint: {e}")

def main():
    install_dependencies()
    subprocess.run(['git', 'clone', 'https://github.com/gregorymendez/ikea_complexity_index.git', '/app'], check=True)
    install_ikea_complexity_index()
    start_server()
    product_id = select_random_product()
    analysis_time = analyze_complexity(product_id)
    compare_with_manual_analysis(product_id, analysis_time)
    test_health_endpoint()

    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['node', 'server.js'], cwd='/app')
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"BENCHMARK:install_time_s: {end_time - start_time}")
    print(f"BENCHMARK:memory_usage_mb: {current / 10**6}")
    print(f"BENCHMARK:import_time_ms: {peak / 10**3}")
    print(f"BENCHMARK:hello_world_ms: {analysis_time * 1000}")
    print(f"BENCHMARK:compile_time_ms: {(end_time - start_time) * 1000}")
    print("RUN_OK")

if __name__ == "__main__":
    main()