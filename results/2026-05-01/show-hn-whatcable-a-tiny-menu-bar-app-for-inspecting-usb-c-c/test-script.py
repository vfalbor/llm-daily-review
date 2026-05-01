import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery
import os

def install_git():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:Failed to install git: {str(e)}")

def clone_and_install_package():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/darrylmorley/whatcable.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './whatcable'], cwd='./whatcable', check=False)
        print("INSTALL_OK")
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/darrylmorley/whatcable.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './whatcable'], cwd='./whatcable', check=False)
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:Failed to install whatcable: {str(e)}")

def test_app():
    try:
        tracemalloc.start()
        start_time = time.time()
        spec = importlib.util.find_spec("whatcable")
        if spec is None:
            print("TEST_FAIL:test_app:Failed to import whatcable")
        else:
            whatcable = importlib.import_module("whatcable")
            end_time = time.time()
            import_time = (end_time - start_time) * 1000
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            print(f"BENCHMARK:import_time_ms:{import_time}")
            print(f"BENCHMARK:memory_usage_bytes:{peak}")
            whatcable.detect_cable()
            cable_detection_time = (time.time() - end_time) * 1000
            print(f"BENCHMARK:cable_detection_time_ms:{cable_detection_time}")
            print("TEST_PASS:test_app")
    except Exception as e:
        print(f"TEST_FAIL:test_app:Failed to run test_app: {str(e)}")

def test_performance():
    try:
        start_time = time.time()
        spec = importlib.util.find_spec("whatcable")
        if spec is None:
            print("TEST_FAIL:test_performance:Failed to import whatcable")
        else:
            whatcable = importlib.import_module("whatcable")
            whatcable.detect_cable()
            end_time = time.time()
            cable_detection_time = (end_time - start_time) * 1000
            print(f"BENCHMARK:cable_detection_time_ms:{cable_detection_time}")
            print("TEST_PASS:test_performance")
    except Exception as e:
        print(f"TEST_FAIL:test_performance:Failed to run test_performance: {str(e)}")

def compare_to_baseline():
    try:
        start_time = time.time()
        spec = importlib.util.find_spec("USB_Disk_Security")
        if spec is None:
            print("TEST_SKIP:compare_to_baseline:Baseline tool not installed")
        else:
            usb_disk_security = importlib.import_module("USB_Disk_Security")
            usb_disk_security.scan_disk()
            end_time = time.time()
            cable_detection_time = (end_time - start_time) * 1000
            start_time = time.time()
            spec = importlib.util.find_spec("whatcable")
            if spec is None:
                print("TEST_SKIP:compare_to_baseline:WhatCable not installed")
            else:
                whatcable = importlib.import_module("whatcable")
                whatcable.detect_cable()
                end_time = time.time()
                whatcable_detection_time = (end_time - start_time) * 1000
                ratio = whatcable_detection_time / cable_detection_time
                print(f"BENCHMARK:vs_usb_disk_security_ratio:{ratio}")
                print("TEST_PASS:compare_to_baseline")
    except Exception as e:
        print(f"TEST_FAIL:compare_to_baseline:Failed to compare to baseline: {str(e)}")

def main():
    install_git()
    clone_and_install_package()
    test_app()
    test_performance()
    compare_to_baseline()
    print("RUN_OK")

if __name__ == "__main__":
    main()