import subprocess
import time
import tracemalloc
import os

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
    try:
        subprocess.run(['pip', 'install', 'gitpython'], check=True)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:gitpython")
        subprocess.run(['git', 'clone', 'https://github.com/gitpython-developers/GitPython.git'], check=True)
        os.chdir('GitPython')
        subprocess.run(['pip', 'install', '-e', '.'], check=True)
        os.chdir('..')

def test_end_of_options_flag():
    try:
        subprocess.run(['git', '--end-of-options', '--', '-a'], check=True)
        print("TEST_PASS:--end-of-options")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:--end-of-options:{str(e)}")

def test_performance_impact():
    try:
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['git', 'status'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:status_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:status_memory_mb:{peak / 10**6}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:performance_impact:{str(e)}")
    else:
        print("TEST_PASS:performance_impact")

def compare_to_baseline():
    try:
        start_time = time.time()
        subprocess.run(['git', 'status'], check=True)
        end_time = time.time()
        git_time = end_time - start_time
        start_time = time.time()
        subprocess.run(['hg', 'status'], check=True)
        end_time = time.time()
        hg_time = end_time - start_time
        print(f"BENCHMARK:vs_hg_status_time_ms:{(git_time / hg_time) * 1000}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_to_baseline:{str(e)}")
    else:
        print("TEST_PASS:compare_to_baseline")

def main():
    install_dependencies()
    print("INSTALL_OK")
    test_end_of_options_flag()
    test_performance_impact()
    compare_to_baseline()
    print("RUN_OK")

if __name__ == "__main__":
    main()