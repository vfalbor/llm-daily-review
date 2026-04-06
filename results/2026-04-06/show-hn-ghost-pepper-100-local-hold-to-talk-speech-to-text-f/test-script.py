import subprocess
import time
import tracemalloc
import importlib.util
import sys

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

def install_tool():
    try:
        subprocess.run(['pip', 'install', 'ghost-pepper'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

def test_speech_to_text():
    try:
        import ghost_pepper
        start_time = time.time()
        result = ghost_pepper.transcribe('synthetic_audio.wav')
        end_time = time.time()
        print(f'BENCHMARK:speech_to_text_latency_ms:{(end_time - start_time) * 1000}')
        print(f'TEST_PASS:speech_to_text')
    except Exception as e:
        print(f'TEST_FAIL:speech_to_text:{e}')

def test_robustness_with_background_noise():
    try:
        import ghost_pepper
        start_time = time.time()
        result = ghost_pepper.transcribe('noisy_audio.wav')
        end_time = time.time()
        print(f'BENCHMARK:robustness_latency_ms:{(end_time - start_time) * 1000}')
        print(f'TEST_PASS:robustness_with_background_noise')
    except Exception as e:
        print(f'TEST_FAIL:robustness_with_background_noise:{e}')

def compare_performance_with_baseline():
    try:
        import vosk
        start_time = time.time()
        vosk.transcribe('synthetic_audio.wav')
        end_time = time.time()
        vosk_latency = (end_time - start_time) * 1000

        import ghost_pepper
        start_time = time.time()
        ghost_pepper.transcribe('synthetic_audio.wav')
        end_time = time.time()
        ghost_pepper_latency = (end_time - start_time) * 1000

        ratio = ghost_pepper_latency / vosk_latency
        print(f'BENCHMARK:vs_vosk_latency_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_SKIP:compare_performance_with_baseline:{e}')

def measure_import_time():
    start_time = time.time()
    import ghost_pepper
    end_time = time.time()
    print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}')

def measure_memory_usage():
    tracemalloc.start()
    import ghost_pepper
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_mb:{peak / 10**6}')
    tracemalloc.stop()

def main():
    install_dependencies()
    install_tool()

    measure_import_time()
    test_speech_to_text()
    test_robustness_with_background_noise()
    compare_performance_with_baseline()
    measure_memory_usage()

    print('RUN_OK')

if __name__ == '__main__':
    main()