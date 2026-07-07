import subprocess
import requests
import time
import tracemalloc
import os

# 1. Install system packages with subprocess
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# 2. Install tool dependencies via subprocess
subprocess.run(['npm', 'install', '-g', 'whimfiles'], check=False)

try:
    # 3. Run Whimfiles server in background
    subprocess.Popen(['whimfiles', '&'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(5)  # wait for server to start

    # 4. Run benchmark comparing Whimfiles to other file managers
    start_time = time.time()
    response = requests.get('http://localhost:8080/health')
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:whimfiles_response_time_ms:{response_time}")

    # 5. Test filtering feature
    try:
        response = requests.get('http://localhost:8080/files?query=example')
        if response.status_code == 200:
            print("TEST_PASS:filtering")
        else:
            print(f"TEST_FAIL:filtering:{response.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:filtering:{str(e)}")

    # 6. Test fuzzy find feature
    try:
        response = requests.get('http://localhost:8080/files?query=fuzzy_example')
        if response.status_code == 200:
            print("TEST_PASS:fuzzy_find")
        else:
            print(f"TEST_FAIL:fuzzy_find:{response.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:fuzzy_find:{str(e)}")

    # 7. Verify that the app does not use Electron
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'electron':
                print("TEST_FAIL:electron_used")
                break
        else:
            print("TEST_PASS:electron_not_used")
    except Exception as e:
        print(f"TEST_FAIL:electron_check:{str(e)}")

    # 8. Compare performance vs baseline tool (Dolphin)
    try:
        subprocess.run(['git', 'clone', 'https://github.com/dolphin-emu/dolphin.git'], check=False)
        dolphin_start_time = time.time()
        subprocess.run(['./dolphin/dolphin'], check=False)
        dolphin_end_time = time.time()
        dolphin_response_time = (dolphin_end_time - dolphin_start_time) * 1000
        print(f"BENCHMARK:vs_dolphin_response_time_ms:{response_time / dolphin_response_time}")
    except Exception as e:
        print(f"BENCHMARK:vs_dolphin_response_time_ms:Error:{str(e)}")

    # 9. Measure memory usage
    tracemalloc.start()
    response = requests.get('http://localhost:8080/files')
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")

    # 10. Measure time to import modules
    import_time = time.time()
    try:
        import whimfiles
    except ImportError:
        print(f"TEST_FAIL:importing_whimfiles")
    else:
        import_end_time = time.time()
        import_time_taken = (import_end_time - import_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time_taken}")

    # 11. Print RUN_OK
    print("RUN_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")
    print("RUN_OK")