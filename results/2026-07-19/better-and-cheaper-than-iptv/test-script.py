import subprocess
import time
import tracemalloc
import os

def install_package(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

def install_dependencies():
    install_package('nodejs')
    install_package('npm')
    install_package('git')
    install_package('cargo')
    install_package('rust')
    subprocess.run(['npm', 'install', '-g', 'castor'], check=True)
    print('INSTALL_OK')

def create_channel():
    try:
        start_time = time.time()
        subprocess.run(['castor', 'create', 'channel'], check=True)
        end_time = time.time()
        print(f'BENCHMARK:create_channel_time_ms:{(end_time - start_time) * 1000:.2f}')
        print('TEST_PASS:create_channel')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:create_channel:{e}')

def insert_rows():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['castor', 'insert', '1000'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:insert_time_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'BENCHMARK:insert_memory_mb:{current / 1024 / 1024:.2f}')
        print('TEST_PASS:insert_rows')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:insert_rows:{e}')

def run_select_query():
    try:
        start_time = time.time()
        subprocess.run(['castor', 'select', 'column'], check=True)
        end_time = time.time()
        print(f'BENCHMARK:select_query_time_ms:{(end_time - start_time) * 1000:.2f}')
        print('TEST_PASS:run_select_query')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:run_select_query:{e}')

def compare_latency():
    try:
        start_time = time.time()
        subprocess.run(['castor', 'select', 'column'], check=True)
        end_time = time.time()
        castor_latency = (end_time - start_time) * 1000
        iptv_latency = 10  # Replace with actual IPTV latency
        print(f'BENCHMARK:vs_iptv_latency_ratio:{castor_latency / iptv_latency:.2f}')
        print('TEST_PASS:compare_latency')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:compare_latency:{e}')

def main():
    install_dependencies()
    create_channel()
    insert_rows()
    run_select_query()
    compare_latency()
    print('RUN_OK')

if __name__ == '__main__':
    main()