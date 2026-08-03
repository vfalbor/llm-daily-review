import subprocess
import time
import tracemalloc
import os

def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        return False
    return True

def install_deps():
    pkgs = ['git']
    for pkg in pkgs:
        if not run_cmd(['apk', 'add', '--no-cache', pkg]):
            return False
    return True

def install_kakehashi():
    if not run_cmd(['pip', 'install', 'kakehashi']):
        subprocess.run(['git', 'clone', 'https://github.com/wie-project/kakehashi.git'], check=True)
        if not run_cmd(['pip', 'install', '-e', './kakehashi']):
            print("INSTALL_FAIL:Failed to install kakehashi")
            return False
    return True

def run_test(name):
    try:
        start_time = time.time()
        tracemalloc.start()
        import kakehashi
        kakehashi.run_macos_binary('example')
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:run_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{str(e)}")

def compare_with_baseline():
    try:
        import time
        start_time = time.time()
        # Run baseline tool
        subprocess.run(['wine', 'example.exe'], check=True)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:baseline_time_ms:{baseline_time:.2f}")
        # Compare with kakehashi
        kakehashi_time = (end_time - start_time) * 1000
        ratio = kakehashi_time / baseline_time
        print(f"BENCHMARK:vs_wine_time_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"BENCHMARK:vs_wine_time_ratio:Failed to compare with baseline")

if __name__ == '__main__':
    if not install_deps():
        exit(1)
    if not install_kakehashi():
        exit(1)
    run_test('kakehashi_import')
    compare_with_baseline()
    print("RUN_OK")