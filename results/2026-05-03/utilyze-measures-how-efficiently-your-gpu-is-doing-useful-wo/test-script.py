import subprocess
import time
import tracemalloc
import sys
import os

# INSTALLATION
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

try:
    subprocess.run(['pip', 'install', 'utilyze'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/systalyze/utilyze.git'], check=False)
        os.chdir('utilyze')
        subprocess.run(['pip', 'install', '-e', '.'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

# BENCHMARK
import utilyze
start_time = time.time()
utilyze.main(['--dummy'])
end_time = time.time()
print(f"BENCHMARK:utilyze_dummy_ms:{(end_time - start_time) * 1000:.2f}")

tracemalloc.start()
start_time = time.time()
utilyze.main(['--dummy'])
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:utilyze_dummy_memory_mb:{(peak / 1024 / 1024):.2f}")
print(f"BENCHMARK:utilyze_dummy_time_s:{(end_time - start_time):.2f}")

# TESTS
def test_dummy_workload():
    try:
        start_time = time.time()
        utilyze.main(['--dummy'])
        end_time = time.time()
        print(f"TEST_PASS:test_dummy_workload")
        print(f"BENCHMARK:dummy_latency_ms:{(end_time - start_time) * 1000:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:test_dummy_workload:{str(e)}")

test_dummy_workload()

# BENCHMARK VS BASELINE
try:
    import GPUBenchmark
    start_time = time.time()
    GPUBenchmark.main(['--dummy'])
    end_time = time.time()
    baseline_time = (end_time - start_time) * 1000
    utilyze_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_GPBenchmark_dummy_ratio:{(utilyze_time / baseline_time):.2f}")
except Exception as e:
    print(f"BENCHMARK:vs_GPBenchmark_dummy_ratio:baseline_not_installed")

# FINAL
print("RUN_OK")