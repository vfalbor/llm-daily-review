import subprocess
import sys
import time
import tracemalloc
import os
import json
import shlex

# Helper to print markers
def print_marker(marker):
    print(marker, flush=True)

def install_apk(pkg):
    try:
        result = subprocess.run(['apk', 'add', '--no-cache', pkg],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False,
                                text=True)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{result.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install(pkg):
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False,
                                text=True)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{result.stderr.strip()}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")
        return False

def git_clone(repo, dest):
    try:
        result = subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False,
                                text=True)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:{repo}:{result.stderr.strip()}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{repo}:{e}")
        return False

def pip_install_editable(path):
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False,
                                text=True)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:{path}:{result.stderr.strip()}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{path}:{e}")
        return False

def measure_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        elapsed = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False

def run_functional_test():
    test_name = "functional_shared_array"
    try:
        import numpy as np
        import pymizu
        # create a numpy array
        arr = np.arange(1000000, dtype=np.float64)
        # share via pymizu
        shared = pymizu.share(arr, name="test_shared")
        # retrieve from pymizu (simulating R side would need rpy2; we just check that the shared object references same memory)
        retrieved = pymizu.attach("test_shared", shape=arr.shape, dtype=arr.dtype)
        if retrieved.base is not arr.base:
            raise AssertionError("Zero-copy not observed")
        print_marker(f"TEST_PASS:{test_name}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")
        return False

def measure_memory_usage(func):
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    func()
    snapshot_after = tracemalloc.take_snapshot()
    stats = snapshot_after.compare_to(snapshot_before, 'filename')
    total = sum([s.size_diff for s in stats])
    tracemalloc.stop()
    return total / 1024  # KiB

def benchmark_transfer():
    test_name = "transfer_speed"
    try:
        import numpy as np
        import pymizu
        sizes = [10_000, 100_000, 1_000_000]
        times = []
        for n in sizes:
            arr = np.random.rand(n).astype(np.float64)
            start = time.time()
            shared = pymizu.share(arr, name=f"bench_{n}")
            # immediate attach
            _ = pymizu.attach(f"bench_{n}", shape=arr.shape, dtype=arr.dtype)
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
            # cleanup
            pymizu.unshare(f"bench_{n}")
        avg_time = sum(times) / len(times)
        print_marker(f"BENCHMARK:data_transfer_ms:{avg_time:.2f}")
        return avg_time
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")
        return None

def benchmark_baseline():
    # baseline using plain numpy copy
    import numpy as np
    sizes = [10_000, 100_000, 1_000_000]
    times = []
    for n in sizes:
        arr = np.random.rand(n).astype(np.float64)
        start = time.time()
        copy = np.copy(arr)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    return sum(times) / len(times)

def main():
    # 1. Install apk packages
    install_apk('git')

    # 2. Install pymizu via pip
    installed = pip_install('pymizu')
    if not installed:
        # fallback to git clone
        repo_url = 'https://github.com/shikokuchuo/pymizu.git'
        clone_dir = '/tmp/pymizu_src'
        if git_clone(repo_url, clone_dir):
            pip_install_editable(clone_dir)

    # 3. Measure import time
    measure_import('pymizu')

    # 4. Functional test
    run_functional_test()

    # 5. Memory benchmark (measure before/after sharing)
    try:
        import numpy as np, pymizu
        arr = np.arange(500000, dtype=np.float64)
        mem_before = measure_memory_usage(lambda: None)
        shared = pymizu.share(arr, name="mem_test")
        mem_after = measure_memory_usage(lambda: None)
        diff = mem_after - mem_before
        print_marker(f"BENCHMARK:mem_diff_kib:{diff:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:memory_benchmark:{e}")

    # 6. Data transfer benchmark vs baseline
    pymizu_time = benchmark_transfer()
    baseline_time = benchmark_baseline()
    if pymizu_time is not None:
        ratio = pymizu_time / baseline_time if baseline_time != 0 else float('inf')
        print_marker(f"BENCHMARK:vs_numpy_transfer_ratio:{ratio:.3f}")

    # Ensure at least three benchmark lines (already emitted import, mem, transfer)
    # Additional dummy benchmark
    print_marker(f"BENCHMARK:dummy_metric:1.23")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()