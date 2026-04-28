import subprocess
import time
import tracemalloc
import os

def install_localsend():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git', 'curl'], check=True)
        subprocess.run(['git', 'clone', 'https://github.com/localsend/localsend.git'], check=True)
        os.chdir('localsend')
        subprocess.run(['git', 'submodule', 'update', '--init'], check=True)
        subprocess.run(['apk', 'add', '--no-cache', 'gcc', 'make'], check=True)
        subprocess.run(['make'], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_file_transfer():
    try:
        start_time = time.time()
        subprocess.run(['./localsend', '--port', '8080'], check=True)
        subprocess.run(['./localsend', '--port', '8081'], check=True)
        subprocess.run(['./localsend', '--send', 'test_file.txt', '--port', '8080'], check=True)
        subprocess.run(['./localsend', '--recv', '--port', '8081'], check=True)
        end_time = time.time()
        print(f'BENCHMARK:file_transfer_time_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:file_transfer')
    except Exception as e:
        print(f'TEST_FAIL:file_transfer:{str(e)}')

def compare_transfer_speed():
    try:
        start_time = time.time()
        subprocess.run(['./localsend', '--port', '8080'], check=True)
        subprocess.run(['./localsend', '--send', '1GB_file.txt', '--port', '8080'], check=True)
        end_time = time.time()
        localsend_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['./airdrop', '--send', '1GB_file.txt'], check=True)
        end_time = time.time()
        airdrop_time = end_time - start_time
        print(f'BENCHMARK:vs_airdrop_1GB_file_ratio:{localsend_time / airdrop_time}')
        print('TEST_PASS:compare_transfer_speed')
    except Exception as e:
        print(f'TEST_FAIL:compare_transfer_speed:{str(e)}')

def test_transfer_success_rate():
    try:
        success_count = 0
        for i in range(5):
            start_time = time.time()
            subprocess.run(['./localsend', '--port', f'808{i}'], check=True)
            subprocess.run(['./localsend', '--send', 'test_file.txt', f'--port', f'808{i}'], check=True)
            subprocess.run(['./localsend', '--recv', f'--port', f'808{i}'], check=True)
            end_time = time.time()
            print(f'BENCHMARK:file_transfer_time_ms:{(end_time - start_time) * 1000}')
            success_count += 1
        print(f'BENCHMARK:transfer_success_rate:{success_count / 5}')
        print('TEST_PASS:transfer_success_rate')
    except Exception as e:
        print(f'TEST_FAIL:transfer_success_rate:{str(e)}')

def main():
    tracemalloc.start()
    install_localsend()
    test_file_transfer()
    compare_transfer_speed()
    test_transfer_success_rate()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{peak}')
    print(f'BENCHMARK:time_taken_s:{time.time() - time.process_time()}')
    print('RUN_OK')

if __name__ == '__main__':
    main()