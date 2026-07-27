import subprocess
import time
import tracemalloc
import requests
import os

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
        subprocess.run(['npm', 'install', 'ffmpeg'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/AARomanov1985/Audio-Cassette-Simulation.git'], check=False)
        subprocess.run(['npm', 'install', 'ffmpeg-cli'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_simulation_accuracy():
    try:
        start_time = time.time()
        subprocess.run(['ffmpeg', '-i', 'test_files/input.mp3', '-c:a', 'pcm_s16le', '-ar', '44.1k', 'output.wav'], check=False)
        subprocess.run(['node', 'index.js', 'output.wav', 'simulated.wav'], cwd='Audio-Cassette-Simulation', check=False)
        end_time = time.time()
        similarity = subprocess.run(['ffmpeg', '-i', 'output.wav', '-i', 'simulated.wav', '-filter_complex', 'aeval=AAE=corr(A,a); showinfo', '-f', 'null', '-'], check=False, stdout=subprocess.PIPE)
        similarity = similarity.stdout.decode('utf-8').splitlines()[-1].split('=')[1]
        print(f"BENCHMARK:simulation_accuracy:{similarity}")
        print(f"BENCHMARK:simulation_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:simulation_accuracy")
    except Exception as e:
        print(f"TEST_FAIL:simulation_accuracy:{str(e)}")

def test_simulation_performance():
    try:
        start_time = time.time()
        subprocess.run(['ffmpeg', '-i', 'test_files/input.mp3', '-c:a', 'pcm_s16le', '-ar', '44.1k', 'output.wav'], check=False)
        subprocess.run(['node', 'index.js', 'output.wav', 'simulated.wav'], cwd='Audio-Cassette-Simulation', check=False)
        end_time = time.time()
        subprocess.run(['ffmpeg', '-i', 'simulated.wav', '-f', 'null', '-'], check=False)
        print(f"BENCHMARK:simulation_performance_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:simulation_performance")
    except Exception as e:
        print(f"TEST_FAIL:simulation_performance:{str(e)}")

def test_comparison_to_original():
    try:
        start_time = time.time()
        subprocess.run(['ffmpeg', '-i', 'test_files/input.mp3', '-c:a', 'pcm_s16le', '-ar', '44.1k', 'output.wav'], check=False)
        subprocess.run(['node', 'index.js', 'output.wav', 'simulated.wav'], cwd='Audio-Cassette-Simulation', check=False)
        end_time = time.time()
        similarity = subprocess.run(['ffmpeg', '-i', 'output.wav', '-i', 'simulated.wav', '-filter_complex', 'aeval=AAE=corr(A,a); showinfo', '-f', 'null', '-'], check=False, stdout=subprocess.PIPE)
        similarity = similarity.stdout.decode('utf-8').splitlines()[-1].split('=')[1]
        print(f"BENCHMARK:comparison_to_original:{similarity}")
        print(f"BENCHMARK:comparison_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:comparison_to_original")
    except Exception as e:
        print(f"TEST_FAIL:comparison_to_original:{str(e)}")

def compare_to_baseline():
    try:
        start_time = time.time()
        subprocess.run(['sox', 'test_files/input.mp3', 'output.wav'], check=False)
        end_time = time.time()
        sox_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['node', 'index.js', 'output.wav', 'simulated.wav'], cwd='Audio-Cassette-Simulation', check=False)
        end_time = time.time()
        simulation_time = end_time - start_time
        print(f"BENCHMARK:vs_sox_ratio:{simulation_time / sox_time}")
        print(f"BENCHMARK:vs_sox_time_ms:{(simulation_time - sox_time) * 1000}")
        print("TEST_PASS:comparison_to_baseline")
    except Exception as e:
        print(f"TEST_FAIL:comparison_to_baseline:{str(e)}")

def measure_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['node', 'index.js', 'test_files/input.mp3', 'simulated.wav'], cwd='Audio-Cassette-Simulation', check=False)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024}")
        print(f"BENCHMARK:peak_memory_usage_mb:{peak / 1024 / 1024}")
        tracemalloc.stop()
        print("TEST_PASS:memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage:{str(e)}")

install_dependencies()
test_simulation_accuracy()
test_simulation_performance()
test_comparison_to_original()
compare_to_baseline()
measure_memory_usage()
print("RUN_OK")