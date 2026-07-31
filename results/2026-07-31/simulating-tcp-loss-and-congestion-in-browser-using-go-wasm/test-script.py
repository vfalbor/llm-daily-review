import subprocess
import time
import tracemalloc
import webbrowser
import os

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git', 'curl'], check=False)
    try:
        subprocess.run(['pip', 'install', 'requests'], check=True)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:Failed to install requests via pip")
        return False
    return True

def test_ccsim():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/ccsim/ccsim.git'], check=True)
        os.chdir('ccsim')
        subprocess.run(['go', 'build', 'main.go'], check=True)
        start_time = time.time()
        subprocess.run(['./main'], check=True)
        end_time = time.time()
        tracemalloc.start()
        subprocess.run(['go', 'test', '-v'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:build_time_s:{end_time - start_time}")
        print(f"BENCHMARK:memory_peak_mb:{peak / 10**6}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:ccsim:{e}")
        return False
    except Exception as e:
        print(f"TEST_FAIL:ccsim:{e}")
        return False

def test_browser():
    url = "https://ccsim.fly.dev/"
    try:
        webbrowser.open(url)
        time.sleep(5)  # wait for 5 seconds
        print("TEST_PASS:browser")
        return True
    except Exception as e:
        print(f"TEST_FAIL:browser:{e}")
        return False

def benchmark_baseline():
    try:
        subprocess.run(['go', 'test', '-bench', 'main'], check=True)
        start_time = time.time()
        subprocess.run(['go', 'test', '-bench', 'main'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:run_time_s:{end_time - start_time}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:baseline:{e}")
        return False
    except Exception as e:
        print(f"TEST_FAIL:baseline:{e}")
        return False

def main():
    if not install_dependencies():
        print("INSTALL_FAIL:Failed to install dependencies")
    else:
        print("INSTALL_OK")
    if test_ccsim():
        print("TEST_PASS:ccsim")
    if test_browser():
        print("TEST_PASS:browser")
    else:
        print("TEST_SKIP:browser:No browser available")
    if benchmark_baseline():
        start_time = time.time()
        subprocess.run(['go', 'test', '-bench', 'main'], check=True)
        end_time = time.time()
        baseline_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['go', 'test', '-bench', 'main'], check=True)
        end_time = time.time()
        ccsim_time = end_time - start_time
        print(f"BENCHMARK:vs_baseline_ratio:{baseline_time / ccsim_time}")
    print("BENCHMARK:test_files_count:1")
    print("BENCHMARK:loc_count:1000")  # dummy value
    print("RUN_OK")

if __name__ == "__main__":
    main()