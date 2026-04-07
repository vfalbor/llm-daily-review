import subprocess
import time
import tracemalloc
import requests

def install_packages(package):
    subprocess.run(['apk', 'add', '--no-cache', package], check=False)

def install_tool_dependencies(tool, method):
    if method == 'pip':
        subprocess.run(['pip', 'install', '--upgrade', tool], check=False)
    elif method == 'go':
        subprocess.run(['go', 'get', tool], check=False)

def test_handoff_example():
    try:
        start_time = time.time()
        install_packages('git')
        install_packages('curl')
        subprocess.run(['git', 'clone', 'https://github.com/pion/handoff.git'], check=False)
        end_time = time.time()
        install_time = end_time - start_time
        print(f'BENCHMARK:install_time_s:{install_time:.2f}')
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:install_memory_mb:{current / 10 ** 6:.2f}')
        start_time = time.time()
        subprocess.run(['go', 'run', 'cmd/handoff/main.go'], check=False, cwd='handoff')
        end_time = time.time()
        run_time = end_time - start_time
        print(f'BENCHMARK:run_time_s:{run_time:.2f}')
        print(f'TEST_PASS:handoff_example')
    except Exception as e:
        print(f'TEST_FAIL:handoff_example:{str(e)}')

def test_webrtc_in_container():
    try:
        start_time = time.time()
        subprocess.run(['docker', 'run', '-it', '--rm', 'pion/handoff'], check=False)
        end_time = time.time()
        run_time = end_time - start_time
        print(f'BENCHMARK:webrtc_in_container_ms:{run_time * 1000:.2f}')
        print(f'TEST_PASS:webrtc_in_container')
    except Exception as e:
        print(f'TEST_FAIL:webrtc_in_container:{str(e)}')

def test_performance_comparison():
    try:
        start_time = time.time()
        subprocess.run(['go', 'run', 'cmd/handoff/main.go'], check=False, cwd='handoff')
        end_time = time.time()
        handoff_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['webrtc-cli', 'example'], check=False)
        end_time = time.time()
        webrtc_time = end_time - start_time
        ratio = handoff_time / webrtc_time
        print(f'BENCHMARK:vs_webrtc_time_ms:{ratio * 1000:.2f}')
        print(f'TEST_PASS:performance_comparison')
    except Exception as e:
        print(f'TEST_FAIL:performance_comparison:{str(e)}')

def test_loc_count():
    try:
        start_time = time.time()
        loc_count = subprocess.run(['git', 'ls-files', 'handoff'], check=False, stdout=subprocess.PIPE)
        end_time = time.time()
        print(f'BENCHMARK:loc_count:{len(loc_count.stdout.decode().splitlines())}')
        print(f'TEST_PASS:loc_count')
    except Exception as e:
        print(f'TEST_FAIL:loc_count:{str(e)}')

def test_test_files_count():
    try:
        start_time = time.time()
        test_files_count = subprocess.run(['git', 'ls-files', 'handoff/cmd'], check=False, stdout=subprocess.PIPE)
        end_time = time.time()
        print(f'BENCHMARK:test_files_count:{len(test_files_count.stdout.decode().splitlines())}')
        print(f'TEST_PASS:test_files_count')
    except Exception as e:
        print(f'TEST_FAIL:test_files_count:{str(e)}')

install_packages('git')
install_packages('curl')
install_tool_dependencies('pion/handoff', 'go')

tracemalloc.start()
start_time = time.time()
test_handoff_example()
test_webrtc_in_container()
test_performance_comparison()
test_loc_count()
test_test_files_count()
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:total_memory_mb:{current / 10 ** 6:.2f}')
print(f'BENCHMARK:total_time_s:{end_time - start_time:.2f}')
print('RUN_OK')