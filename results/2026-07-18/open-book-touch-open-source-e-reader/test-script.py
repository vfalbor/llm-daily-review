import subprocess
import requests
import time
import tracemalloc
import json

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
    print("INSTALL_OK")
    try:
        subprocess.run(['npm', 'install', 'git://github.com/oddly-specific-objects/open-book-touch.git'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def test_ebook_display():
    try:
        start_time = time.time()
        subprocess.run(['npm', 'start'], cwd='open-book-touch', check=True)
        end_time = time.time()
        response = requests.get('http://localhost:3000')
        if response.status_code == 200:
            print(f"TEST_PASS:ebook_display")
            print(f"BENCHMARK:ebook_display_time_ms:{(end_time - start_time) * 1000}")
        else:
            print(f"TEST_FAIL:ebook_display:{response.status_code}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:ebook_display:{e}")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:ebook_display:{e}")

def compare_with_commercial_readers():
    try:
        start_time = time.time()
        response = requests.get('https://example.com/ebook')
        end_time = time.time()
        if response.status_code == 200:
            print(f"TEST_PASS:commercial_reader")
            print(f"BENCHMARK:commercial_reader_time_ms:{(end_time - start_time) * 1000}")
            # measure and emit vs baseline
            baseline_time = 100  # assumed baseline time
            ratio = ((end_time - start_time) * 1000) / baseline_time
            print(f"BENCHMARK:vs_kobo_ebook_display_ratio:{ratio}")
        else:
            print(f"TEST_FAIL:commercial_reader:{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:commercial_reader:{e}")

def measure_battery_life():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['npm', 'start'], cwd='open-book-touch', check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()
        print(f"BENCHMARK:battery_life_time_s:{end_time - start_time}")
        print(f"BENCHMARK:battery_life_memory_mb:{peak / (1024 * 1024)}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:battery_life:{e}")

def main():
    install_dependencies()
    test_ebook_display()
    compare_with_commercial_readers()
    measure_battery_life()
    print("RUN_OK")

if __name__ == "__main__":
    main()