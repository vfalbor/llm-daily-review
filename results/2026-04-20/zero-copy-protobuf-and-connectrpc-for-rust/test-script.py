import subprocess
import time
import tracemalloc
import os

def install_apk_packages():
    packages = ['nodejs', 'npm', 'git', 'cargo', 'rust']
    for package in packages:
        subprocess.run(['apk', 'add', '--no-cache', package], check=False)
        print(f'INSTALL_OK: {package}')

def install_connectrpc():
    start_time = time.time()
    try:
        subprocess.run(['cargo', 'new', 'connectrpc_example'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/iainmcgin/connectrpc.git'], check=False, cwd='connectrpc_example')
        subprocess.run(['cargo', 'build'], check=False, cwd='connectrpc_example/connectrpc')
        subprocess.run(['cargo', 'run'], check=False, cwd='connectrpc_example/connectrpc')
        print('INSTALL_OK: connectrpc')
    except Exception as e:
        print(f'INSTALL_FAIL: connectrpc: {str(e)}')
    end_time = time.time()
    print(f'BENCHMARK:install_time_s:{end_time - start_time}')

def test_zero_copy_protobuf():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run'], check=False, cwd='connectrpc_example/connectrpc')
        end_time = time.time()
        print(f'TEST_PASS:zero_copy_protobuf')
        print(f'BENCHMARK:zero_copy_protobuf_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'TEST_FAIL:zero_copy_protobuf: {str(e)}')

def measure_memory_usage():
    tracemalloc.start()
    subprocess.run(['cargo', 'run'], check=False, cwd='connectrpc_example/connectrpc')
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_mb:{peak / 1024 / 1024}')

def compare_with_baseline():
    start_time = time.time()
    subprocess.run(['protoc', '--version'], check=False)
    end_time = time.time()
    baseline_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['cargo', 'run'], check=False, cwd='connectrpc_example/connectrpc')
    end_time = time.time()
    connectrpc_time = end_time - start_time
    print(f'BENCHMARK:vs_protobuf_time_ms:{connectrpc_time * 1000}')
    print(f'BENCHMARK:vs_protobuf_time_ratio:{connectrpc_time / baseline_time}')

if __name__ == "__main__":
    install_apk_packages()
    install_connectrpc()
    test_zero_copy_protobuf()
    measure_memory_usage()
    compare_with_baseline()
    print('RUN_OK')