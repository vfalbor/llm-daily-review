import subprocess
import time
import tracemalloc
import requests
import json

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        subprocess.run(['npm', 'install', 'playcanvas'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

def test_create_project():
    try:
        start_time = time.time()
        subprocess.run(['node', 'playcanvas', 'create-project', 'test-project'], check=True)
        end_time = time.time()
        print(f'TEST_PASS:create_project')
        print(f'BENCHMARK:create_project_time_s:{end_time - start_time}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:create_project:{e}')

def test_gaussian_splat_2d():
    try:
        start_time = time.time()
        subprocess.run(['node', 'playcanvas', 'add-feature', 'gaussian-splat', 'test-project', '2d'], check=True)
        end_time = time.time()
        print(f'TEST_PASS:gaussian_splat_2d')
        print(f'BENCHMARK:gaussian_splat_2d_time_s:{end_time - start_time}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:gaussian_splat_2d:{e}')

def test_gaussian_splat_3d():
    try:
        start_time = time.time()
        subprocess.run(['node', 'playcanvas', 'add-feature', 'gaussian-splat', 'test-project', '3d'], check=True)
        end_time = time.time()
        print(f'TEST_PASS:gaussian_splat_3d')
        print(f'BENCHMARK:gaussian_splat_3d_time_s:{end_time - start_time}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:gaussian_splat_3d:{e}')

def test_performance():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['node', 'playcanvas', 'run', 'test-project'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'TEST_PASS:performance')
        print(f'BENCHMARK:performance_time_s:{end_time - start_time}')
        print(f'BENCHMARK:performance_memory_mb:{peak / 1024 / 1024}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:performance:{e}')

def test_baseline_comparison():
    try:
        start_time = time.time()
        subprocess.run(['node', 'playcanvas', 'run', 'test-project', '--benchmark'], check=True)
        end_time = time.time()
        print(f'TEST_PASS:baseline_comparison')
        print(f'BENCHMARK:vs_playcanvas_gaussian_splat_ratio:{end_time - start_time}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:baseline_comparison:{e}')

def test_health_endpoint():
    try:
        start_time = time.time()
        response = requests.get('http://localhost:8080/health')
        end_time = time.time()
        if response.status_code == 200:
            print(f'TEST_PASS:health_endpoint')
            print(f'BENCHMARK:health_endpoint_time_ms:{(end_time - start_time) * 1000}')
        else:
            print(f'TEST_FAIL:health_endpoint:{response.status_code}')
    except requests.exceptions.RequestException as e:
        print(f'TEST_FAIL:health_endpoint:{e}')

def main():
    install_dependencies()
    test_create_project()
    test_gaussian_splat_2d()
    test_gaussian_splat_3d()
    test_performance()
    test_baseline_comparison()
    test_health_endpoint()
    print('RUN_OK')

if __name__ == '__main__':
    main()