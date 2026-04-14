import subprocess
import time
import tracemalloc
import requests

def install_wiifin():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        subprocess.run(['npm', 'install', '-g', 'wiifin'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        return False
    return True

def start_wiifin_server():
    try:
        subprocess.run(['wiifin', '--start'], check=True)
        print("BENCHMARK:wiifin_start_time_ms:{}".format(int(time.time() * 1000)))
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:start_wiifin_server:{e}")
        return False
    return True

def connect_to_jellyfin_server():
    try:
        response = requests.get('http://localhost:8096/health')
        print("BENCHMARK:health_check_ms:{}".format(int(response.elapsed.total_seconds() * 1000)))
        print("TEST_PASS:connect_to_jellyfin_server")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:connect_to_jellyfin_server:{e}")
        return False
    return True

def play_media_item():
    try:
        response = requests.get('http://localhost:8096/api/items/1234/play')
        print("BENCHMARK:play_media_item_ms:{}".format(int(response.elapsed.total_seconds() * 1000)))
        print("TEST_PASS:play_media_item")
    except requests.exceptions.RequestException as e:
        print(f"TEST_FAIL:play_media_item:{e}")
        return False
    return True

def compare_performance():
    try:
        # Start native Wii browser
        subprocess.run(['wiibrowse'], check=True)
        time.sleep(2)  # give browser time to start
        response = requests.get('http://localhost:8096/health')
        print("BENCHMARK:browser_health_check_ms:{}".format(int(response.elapsed.total_seconds() * 1000)))
        print("BENCHMARK:vs_wiifin_health_check_ratio:{}".format(int(response.elapsed.total_seconds() * 1000) / 100))
        print("TEST_PASS:compare_performance")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_performance:{e}")
        return False
    return True

def run_wiifin_with_plugins():
    try:
        subprocess.run(['wiifin', '--with-plugins'], check=True)
        print("BENCHMARK:wiifin_with_plugins_start_time_ms:{}".format(int(time.time() * 1000)))
        print("TEST_PASS:run_wiifin_with_plugins")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_wiifin_with_plugins:{e}")
        return False
    return True

def memory_benchmark():
    tracemalloc.start()
    time.sleep(1)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print("BENCHMARK:memory_usage_mb:{}".format(current / (1024 * 1024)))

if __name__ == "__main__":
    if install_wiifin():
        time.sleep(1)  # give wiifin time to start
        if start_wiifin_server():
            connect_to_jellyfin_server()
            play_media_item()
            compare_performance()
            run_wiifin_with_plugins()
        memory_benchmark()
        loc_count = len(subprocess.run(['find', '/usr/lib/node_modules/wiifin'], check=True, stdout=subprocess.PIPE).stdout.splitlines()) - 1
        print("BENCHMARK:loc_count:{}".format(loc_count))
        test_files_count = len(subprocess.run(['find', '/usr/lib/node_modules/wiifin/test'], check=True, stdout=subprocess.PIPE).stdout.splitlines()) - 1
        print("BENCHMARK:test_files_count:{}".format(test_files_count))
    print("RUN_OK")