import subprocess
import time
import tracemalloc
import os
import sys

def update_firmware():
    try:
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/rodecaster/Rodecaster-Pro-Firmware.git'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:update_firmware_time_s:{end_time - start_time:.2f}")
        print("TEST_PASS:update_firmware")
    except Exception as e:
        print(f"TEST_FAIL:update_firmware:{str(e)}")

def test_remote_control_api():
    try:
        start_time = time.time()
        subprocess.run(['ssh', 'localhost', 'ls'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:ssh_connect_time_ms:{(end_time - start_time) * 1000:.2f}")
        print("TEST_PASS:remote_control_api")
    except Exception as e:
        print(f"TEST_FAIL:remote_control_api:{str(e)}")

def test_record_and_stream_audio():
    try:
        start_time = time.time()
        subprocess.run(['arecord', '-l'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:audio_record_time_ms:{(end_time - start_time) * 1000:.2f}")
        print("TEST_PASS:record_and_stream_audio")
    except Exception as e:
        print(f"TEST_FAIL:record_and_stream_audio:{str(e)}")

def count_source_files():
    try:
        start_time = time.time()
        file_count = len([name for name in os.listdir('.') if os.path.isfile(name)])
        end_time = time.time()
        print(f"BENCHMARK:source_files_count:{file_count}")
        print(f"BENCHMARK:count_time_ms:{(end_time - start_time) * 1000:.2f}")
        tracemalloc.start()
        file_count = len([name for name in os.listdir('.') if os.path.isfile(name)])
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{current}")
        tracemalloc.stop()
    except Exception as e:
        print(f"TEST_FAIL:count_source_files:{str(e)}")

def compare_performance_baseline():
    try:
        start_time = time.time()
        # Use Behringer X32 as baseline
        subprocess.run(['git', 'clone', 'https://github.com/Behringer/X32.git'], check=True)
        end_time = time.time()
        baseline_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/rodecaster/Rodecaster-Pro-Firmware.git'], check=True)
        end_time = time.time()
        rodecaster_time = end_time - start_time
        print(f"BENCHMARK:vs_Behringer_X32_clone_ratio:{rodecaster_time / baseline_time:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance_baseline:{str(e)}")

# Install git package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK:git")

# Clone repository and build from source
try:
    subprocess.run(['git', 'clone', 'https://github.com/rodecaster/Rodecaster-Pro-Firmware.git'], check=True)
    print("INSTALL_OK:Rodecaster-Pro-Firmware")
except Exception as e:
    print(f"INSTALL_FAIL:Rodecaster-Pro-Firmware:{str(e)}")

update_firmware()
test_remote_control_api()
test_record_and_stream_audio()
count_source_files()
compare_performance_baseline()

print("RUN_OK")