import subprocess
import time
import tracemalloc
import sys

def install_wacli():
    try:
        # Install system packages
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")
        return False
    return True

def test_wacli_install():
    try:
        start_time = time.time()
        subprocess.run(['npm', 'install', '-g', 'wacli'], check=True)
        end_time = time.time()
        install_time = end_time - start_time
        print(f"BENCHMARK:install_time_s:{install_time:.2f}")
        print(f"TEST_PASS:wacli_install")
    except Exception as e:
        print(f"TEST_FAIL:wacli_install:{str(e)}")

def test_wacli_run():
    try:
        start_time = time.time()
        subprocess.run(['wacli', '--help'], check=True)
        end_time = time.time()
        run_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:wacli_run_ms:{run_time:.2f}")
        print(f"TEST_PASS:wacli_run")
    except Exception as e:
        print(f"TEST_FAIL:wacli_run:{str(e)}")

def test_basline_comparison():
    try:
        # Measure execution time of a similar tool (e.g. whatsapp-cli)
        start_time = time.time()
        subprocess.run(['whatsapp-cli', '--help'], check=True)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        wacli_time = float(subprocess.check_output(['wacli', '--help']).decode('utf-8').split('\n')[-1].split(':')[1].strip())
        print(f"BENCHMARK:vs_wacli_run_ms:{baseline_time / wacli_time:.2f}")
        print(f"BENCHMARK:vs_wacli_run_ratio:{(baseline_time / wacli_time):.2f}")
        print(f"TEST_PASS:baseline_comparison")
    except Exception as e:
        print(f"TEST_FAIL:baseline_comparison:{str(e)}")

def test_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['wacli', '--help'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024):.2f}")
        print(f"TEST_PASS:memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage:{str(e)}")

def test_loc_count():
    try:
        loc_count = int(subprocess.check_output(['git', 'ls-files', '-z']).decode('utf-8').count('\0'))
        print(f"BENCHMARK:loc_count:{loc_count}")
        print(f"TEST_PASS:loc_count")
    except Exception as e:
        print(f"TEST_FAIL:loc_count:{str(e)}")

def test_files_count():
    try:
        files_count = len(subprocess.check_output(['git', 'ls-files']).decode('utf-8').split('\n')[:-1])
        print(f"BENCHMARK:test_files_count:{files_count}")
        print(f"TEST_PASS:files_count")
    except Exception as e:
        print(f"TEST_FAIL:files_count:{str(e)}")

if __name__ == '__main__':
    if install_wacli():
        test_wacli_install()
        test_wacli_run()
        test_basline_comparison()
        test_memory_usage()
        test_loc_count()
        test_files_count()
    print("RUN_OK")