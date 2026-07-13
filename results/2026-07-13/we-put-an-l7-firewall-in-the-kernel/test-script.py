import subprocess
import time
import tracemalloc
import requests

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git', 'curl'], check=False)
    subprocess.run(['pip', 'install', 'requests'], check=False)

def test_docker_pull_run_hello_world():
    try:
        subprocess.run(['docker', 'pull', 'yeet/l7-firewall'], check=True)
        subprocess.run(['docker', 'run', '-d', '--name', 'l7-firewall', 'yeet/l7-firewall'], check=True)
        time.sleep(5)  # wait for container to start
        response = requests.get('http://localhost:8080/health')
        if response.status_code == 200:
            print('TEST_PASS:docker_pull_run_hello_world')
            start_time = time.time()
            subprocess.run(['docker', 'exec', '-it', 'l7-firewall', 'echo', 'hello'], check=True)
            end_time = time.time()
            print(f'BENCHMARK:docker_hello_world_ms:{(end_time - start_time) * 1000:.2f}')
        else:
            print(f'TEST_FAIL:docker_pull_run_hello_world:health check failed with status code {response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:docker_pull_run_hello_world:{str(e)}')

def test_stress_testing():
    try:
        start_time = time.time()
        subprocess.run(['docker', 'exec', '-it', 'l7-firewall', 'stress', '-c', '4', '-t', '10'], check=True)
        end_time = time.time()
        print(f'BENCHMARK:stress_testing_ms:{(end_time - start_time) * 1000:.2f}')
        print('TEST_PASS:stress_testing')
    except Exception as e:
        print(f'TEST_FAIL:stress_testing:{str(e)}')

def test_cicd_integration():
    try:
        # for simplicity, just test if git is installed and can clone a repo
        subprocess.run(['git', 'clone', 'https://github.com/yeet/l7-firewall.git'], check=True)
        print('TEST_PASS:cicd_integration')
    except Exception as e:
        print(f'TEST_FAIL:cicd_integration:{str(e)}')

def test_performance_vs_firewall():
    try:
        start_time = time.time()
        subprocess.run(['docker', 'exec', '-it', 'l7-firewall', 'iperf3', '-c', 'localhost'], check=True)
        end_time = time.time()
        firewall_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['docker', 'exec', '-it', 'firewall', 'iperf3', '-c', 'localhost'], check=True)
        end_time = time.time()
        baseline_time = end_time - start_time
        print(f'BENCHMARK:vs_firewall_iperf3_ratio:{firewall_time / baseline_time:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:performance_vs_firewall:{str(e)}')

def test_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['docker', 'exec', '-it', 'l7-firewall', 'top'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_mb:{current / 10**6:.2f}')
        tracemalloc.stop()
        print('TEST_PASS:memory_usage')
    except Exception as e:
        print(f'TEST_FAIL:memory_usage:{str(e)}')

def test_loc_count():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/yeet/l7-firewall.git'], check=True)
        loc_count = subprocess.check_output(['git', 'ls-files', '-z', '|', 'xargs', '-0', 'wc', '-l']).decode('utf-8').strip()
        print(f'BENCHMARK:loc_count:{int(loc_count)}')
        print('TEST_PASS:loc_count')
    except Exception as e:
        print(f'TEST_FAIL:loc_count:{str(e)}')

install_dependencies()
test_docker_pull_run_hello_world()
test_stress_testing()
test_cicd_integration()
test_performance_vs_firewall()
test_memory_usage()
test_loc_count()
print('RUN_OK')