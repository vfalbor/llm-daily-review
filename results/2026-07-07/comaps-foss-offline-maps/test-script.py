import subprocess
import importlib.util
import importlib.machinery
import time
import tracemalloc
import pkg_resources

def install_package(package_name):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package_name], check=False)
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:Failed to install {package_name} with error: {e}")
        return False

def install_pip_package(package_name):
    try:
        subprocess.run(['pip', 'install', package_name], check=False)
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:Failed to install {package_name} with pip with error: {e}")
        return False

def install_git_package(package_name, repository_url):
    try:
        subprocess.run(['git', 'clone', repository_url], check=False)
        subprocess.run(['pip', 'install', '-e', './comaps'], check=False)
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:Failed to install {package_name} from git with error: {e}")
        return False

def test_map_tile_rendering():
    try:
        import comaps
        tracemalloc.start()
        start_time = time.time()
        comaps.render_map_tile(0, 0, 0)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:map_tile_rendering_latency_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:map_tile_rendering_memory_mb:{peak / 10**6}")
        print("TEST_PASS:map_tile_rendering")
    except Exception as e:
        print(f"TEST_FAIL:map_tile_rendering:{e}")

def test_search_functionality():
    try:
        import comaps
        tracemalloc.start()
        start_time = time.time()
        comaps.search("New York")
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:search_functionality_latency_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:search_functionality_memory_mb:{peak / 10**6}")
        print("TEST_PASS:search_functionality")
    except Exception as e:
        print(f"TEST_FAIL:search_functionality:{e}")

def test_import_time():
    try:
        start_time = time.time()
        import comaps
        end_time = time.time()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:import_time:{e}")

def compare_with_baseline():
    try:
        import osmand
        tracemalloc.start()
        start_time = time.time()
        osmand.render_map_tile(0, 0, 0)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        comaps_time = float([line.split(':')[1] for line in sys.stdout.getvalue().decode().splitlines() if line.startswith('BENCHMARK:map_tile_rendering_latency_ms:')][0])
        osmand_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_osmand_map_tile_rendering_latency_ms:{comaps_time / osmand_time}")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_baseline:{e}")

if __name__ == "__main__":
    print("Start installation")
    if not install_package('git'):
        print("INSTALL_FAIL:Failed to install git")
    if not install_pip_package('comaps'):
        if not install_git_package('comaps', 'https://github.com/comaps/comaps.git'):
            print("INSTALL_FAIL:Failed to install comaps")
    print("INSTALL_OK")

    test_import_time()
    test_map_tile_rendering()
    test_search_functionality()
    compare_with_baseline()

    print("RUN_OK")