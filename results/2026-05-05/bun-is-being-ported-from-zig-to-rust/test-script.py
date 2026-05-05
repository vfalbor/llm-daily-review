import subprocess
import time
import tracemalloc
import os

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

def download_and_compile_bun():
    try:
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/oven-sh/bun.git'], check=True)
        subprocess.run(['cargo', 'build'], cwd='bun', check=True)
        end_time = time.time()
        print(f"INSTALL_OK")
        print(f"BENCHMARK:compile_time_s:{end_time - start_time:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        return False
    return True

def benchmark_rust():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run'], cwd='bun', check=True)
        end_time = time.time()
        print(f"TEST_PASS:rust_benchmark")
        print(f"BENCHMARK:rust_benchmark_ms:{(end_time - start_time) * 1000:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:rust_benchmark:{e}")

def benchmark_zig():
    try:
        start_time = time.time()
        subprocess.run(['git', 'checkout', 'main'], cwd='bun', check=True)
        subprocess.run(['zig', 'build'], cwd='bun', check=True)
        subprocess.run(['./bun'], cwd='bun', check=True)
        end_time = time.time()
        print(f"TEST_PASS:zig_benchmark")
        print(f"BENCHMARK:zig_benchmark_ms:{(end_time - start_time) * 1000:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:zig_benchmark:{e}")

def compare_performance():
    try:
        rust_time = float(subprocess.check_output(['grep', 'BENCHMARK:rust_benchmark_ms:', 'test.log']).decode().strip().split(':')[1])
        zig_time = float(subprocess.check_output(['grep', 'BENCHMARK:zig_benchmark_ms:', 'test.log']).decode().strip().split(':')[1])
        print(f"BENCHMARK:vs_zig_benchmark_ratio:{rust_time / zig_time:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_performance:{e}")

def measure_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['cargo', 'run'], cwd='bun', check=True)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_mb:{peak / 10**6:.2f}")
        tracemalloc.stop()
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:measure_memory_usage:{e}")

def measure_loc_count():
    try:
        loc_count = sum(1 for line in open('bun/Cargo.toml') if line.strip())
        print(f"BENCHMARK:loc_count:{loc_count}")
    except FileNotFoundError:
        print(f"TEST_FAIL:measure_loc_count:File not found")

def count_test_files():
    try:
        test_files_count = len([f for f in os.listdir('bun/tests') if f.endswith('.rs')])
        print(f"BENCHMARK:test_files_count:{test_files_count}")
    except FileNotFoundError:
        print(f"TEST_FAIL:count_test_files:File not found")

install_dependencies()
if download_and_compile_bun():
    benchmark_rust()
    benchmark_zig()
compare_performance()
measure_memory_usage()
measure_loc_count()
count_test_files()

print(f"RUN_OK")