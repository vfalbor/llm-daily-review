import subprocess
import time
import tracemalloc
import os

def run_benchmark(name):
    start_time = time.time()
    tracemalloc.start()
    try:
        yield
    finally:
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:{name}_time_s:{end_time - start_time:.2f}")
        print(f"BENCHMARK:{name}_memory_peak_mb:{peak / 1024 / 1024:.2f}")

def test_install_libusb():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'libusb'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:libusb installation failed ({e})")

def test_clone_repo():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/werwolv/usb4swdevs.git'], check=True)
        print("TEST_PASS:clone_repo")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:clone_repo:Git clone failed ({e})")

def test_count_source_files():
    try:
        with open('usb4swdevs/README.md', 'r') as f:
            lines = f.readlines()
        print(f"BENCHMARK:loc_count:{len(lines)}")
        print(f"BENCHMARK:test_files_count:{len(os.listdir('usb4swdevs'))}")
    except Exception as e:
        print(f"TEST_FAIL:count_source_files:Failed to count source files ({e})")

def test_run_python_examples():
    try:
        subprocess.run(['python', '-c', 'import os'], check=True)
        print("TEST_PASS:run_python_examples")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_python_examples:Python examples failed to run ({e})")

def test_compare_vs_libusb():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'libusb-dev'], check=True)
        subprocess.run(['git', 'clone', 'https://github.com/libusb/libusb.git'], check=True)
        libusb_time = subprocess.run(['time', 'make', '-C', 'libusb'], capture_output=True, text=True).stdout
        libusb_time = float(libusb_time.split('\n')[-2].split(' ')[-1].strip())
        usb4swdevs_time = subprocess.run(['time', 'make', '-C', 'usb4swdevs'], capture_output=True, text=True).stdout
        usb4swdevs_time = float(usb4swdevs_time.split('\n')[-2].split(' ')[-1].strip())
        print(f"BENCHMARK:vs_libusb_compile_time_ratio:{usb4swdevs_time / libusb_time:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:compare_vs_libusb:Failed to compare with libusb ({e})")

def main():
    test_install_libusb()
    with run_benchmark('clone_repo_time'):
        test_clone_repo()
    test_count_source_files()
    with run_benchmark('run_python_examples_time'):
        test_run_python_examples()
    test_compare_vs_libusb()
    print("RUN_OK")

if __name__ == "__main__":
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    main()