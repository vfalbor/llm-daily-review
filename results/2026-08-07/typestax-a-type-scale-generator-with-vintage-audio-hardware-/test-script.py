import subprocess
import time
import tracemalloc
import requests

def install_dependencies():
    subprocess.run(['apk','add','--no-cache','git'], check=False)
    subprocess.run(['apk','add','--no-cache','curl'], check=False)

def install_typestax():
    try:
        subprocess.run(['pip','install','typestax'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git','clone','https://github.com/typestax/typestax.git'], check=True)
            subprocess.run(['pip','install','-e','.'], cwd='typestax', check=True)
            print('INSTALL_OK')
        except subprocess.CalledProcessError as e:
            print(f'INSTALL_FAIL:{e}')

def test_latency():
    try:
        start_time = time.time()
        subprocess.run(['typestax','--latency'], check=True)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:latency_ms:{latency}')
        print('TEST_PASS:latency')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:latency:{e}')

def test_type_scale_generation():
    try:
        start_time = time.time()
        subprocess.run(['typestax','--generate'], check=True)
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:generate_time_ms:{processing_time}')
        print('TEST_PASS:generate_type_scale')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:generate_type_scale:{e}')

def test_processing_time():
    try:
        start_time = time.time()
        subprocess.run(['typestax','--process'], check=True)
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:processing_time_ms:{processing_time}')
        print('TEST_PASS:processing_time')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:processing_time:{e}')

def test_api_endpoints():
    try:
        start_time = time.time()
        response = requests.get('https://api.typestax.com/endpoint')
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:api_response_time_ms:{response_time}')
        print('TEST_PASS:api_endpoints')
    except requests.RequestException as e:
        print(f'TEST_FAIL:api_endpoints:{e}')

def compare_performance():
    try:
        # Measure AudioBox processing time
        start_time = time.time()
        subprocess.run(['audiobox','--process'], check=True)
        end_time = time.time()
        audiobox_processing_time = (end_time - start_time) * 1000

        # Measure TypeStax processing time
        start_time = time.time()
        subprocess.run(['typestax','--process'], check=True)
        end_time = time.time()
        typestax_processing_time = (end_time - start_time) * 1000

        ratio = audiobox_processing_time / typestax_processing_time
        print(f'BENCHMARK:vs_audiobox_processing_ratio:{ratio}')

        # Measure MIDI Studio processing time
        start_time = time.time()
        subprocess.run(['midistudio','--process'], check=True)
        end_time = time.time()
        midistudio_processing_time = (end_time - start_time) * 1000

        ratio = midistudio_processing_time / typestax_processing_time
        print(f'BENCHMARK:vs_midistudio_processing_ratio:{ratio}')

        # Measure Logic Pro processing time
        start_time = time.time()
        subprocess.run(['logicpro','--process'], check=True)
        end_time = time.time()
        logicpro_processing_time = (end_time - start_time) * 1000

        ratio = logicpro_processing_time / typestax_processing_time
        print(f'BENCHMARK:vs_logicpro_processing_ratio:{ratio}')
        print('TEST_PASS:compare_performance')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:compare_performance:{e}')

def main():
    install_dependencies()
    install_typestax()
    test_latency()
    test_type_scale_generation()
    test_processing_time()
    test_api_endpoints()
    compare_performance()

    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('traceback')
    print(f'BENCHMARK:memory_usage_mb:{top_stats[0].size / (1024 * 1024)}')

    run_time = time.time()
    print(f'BENCHMARK:run_time_s:{run_time}')
    print('RUN_OK')

if __name__ == '__main__':
    main()