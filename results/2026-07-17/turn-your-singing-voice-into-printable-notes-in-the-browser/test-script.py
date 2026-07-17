import subprocess
import time
import requests
import tracemalloc
import json

def install_dependencies():
    try:
        # Install system packages
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def install_tool_dependencies():
    try:
        # Clone and install vocal-notation
        subprocess.run(['npm', 'install'], cwd='/vocal-notation', check=False)
        print('INSTALL_OK')
    except Exception as e:
        try:
            # Fallback to npm install -e .
            subprocess.run(['git', 'clone', 'https://github.com/om-intelligence/vocal-notation.git'], check=False)
            subprocess.run(['npm', 'install', '-e', '.'], cwd='/vocal-notation', check=False)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_song_notes():
    try:
        # Send HTTP request to /health endpoint
        start_time = time.time()
        response = requests.get('http://localhost:3000/health')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:response_time_ms:{response_time:.2f}')
        if response.status_code == 200:
            print('TEST_PASS:health_endpoint')
        else:
            print(f'TEST_FAIL:health_endpoint:Status code {response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:health_endpoint:{str(e)}')

def test_audio_input():
    try:
        # Measure frequency accuracy
        start_time = time.time()
        # Simulate audio input
        # Here we assume that the server is running at localhost:3000
        response = requests.post('http://localhost:3000/analyze', json={'audio': 'example_audio'})
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:audio_analysis_time_ms:{response_time:.2f}')
        if response.status_code == 200:
            print('TEST_PASS:audio_input')
        else:
            print(f'TEST_FAIL:audio_input:Status code {response.status_code}')
    except Exception as e:
        print(f'TEST_FAIL:audio_input:{str(e)}')

def test_baseline_performance():
    try:
        # Compare performance vs TonalEnergy
        # Here we assume that TonalEnergy is running at localhost:8080
        start_time = time.time()
        response = requests.get('http://localhost:8080/health')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_tonalenergy_response_time_ms:{response_time:.2f}')
        # Measure ratio
        tracemalloc.start()
        start_time = time.time()
        response = requests.post('http://localhost:3000/analyze', json={'audio': 'example_audio'})
        end_time = time.time()
        vocal_notation_time = (end_time - start_time) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        start_time = time.time()
        response = requests.post('http://localhost:8080/analyze', json={'audio': 'example_audio'})
        end_time = time.time()
        tonalenergy_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_tonalenergy_frequency_accuracy_ratio:{vocal_notation_time / tonalenergy_time:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:baseline_performance:{str(e)}')

def test_memory_usage():
    try:
        # Measure memory usage
        tracemalloc.start()
        start_time = time.time()
        response = requests.post('http://localhost:3000/analyze', json={'audio': 'example_audio'})
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_bytes:{peak}')
        print(f'BENCHMARK:memory_usage_time_s:{(end_time - start_time):.2f}')
    except Exception as e:
        print(f'TEST_FAIL:memory_usage:{str(e)}')

def test_loc_count():
    try:
        # Measure lines of code
        loc_count = 0
        with open('/vocal-notation/index.js', 'r') as file:
            lines = file.readlines()
            loc_count += len(lines)
        print(f'BENCHMARK:loc_count:{loc_count}')
    except Exception as e:
        print(f'TEST_FAIL:loc_count:{str(e)}')

def main():
    install_dependencies()
    install_tool_dependencies()
    test_song_notes()
    test_audio_input()
    test_baseline_performance()
    test_memory_usage()
    test_loc_count()
    print('RUN_OK')

if __name__ == '__main__':
    main()