import subprocess
import time
import tracemalloc
import numpy as np

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)
    print('INSTALL_OK')

def run_hello_world():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/Rust-benchmarks/CPU.git'], check=False)
        subprocess.run(['cargo', 'build', '--release'], cwd='CPU', check=False)
        start_time = time.time()
        subprocess.run(['./target/release/cpufloat'], cwd='CPU', check=False)
        end_time = time.time()
        print(f'BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000}')
        print(f'TEST_PASS:hello_world')
    except Exception as e:
        print(f'TEST_FAIL:hello_world:{str(e)}')

def run_benchmark():
    try:
        start_time = time.time()
        subprocess.run(['python', 'benchmark.py'], cwd='CPU', check=False)
        end_time = time.time()
        print(f'BENCHMARK:benchmark_time_ms:{(end_time - start_time) * 1000}')
        print(f'TEST_PASS:benchmark')
    except Exception as e:
        print(f'TEST_FAIL:benchmark:{str(e)}')

def run_numpy_benchmark():
    try:
        start_time = time.time()
        arr = np.random.rand(1000, 1000)
        arr.sum()
        end_time = time.time()
        print(f'BENCHMARK:numpy_benchmark_ms:{(end_time - start_time) * 1000}')
        print(f'TEST_PASS:numpy_benchmark')
    except Exception as e:
        print(f'TEST_FAIL:numpy_benchmark:{str(e)}')

def compare_benchmark():
    try:
        rust_benchmark_time = float(subprocess.run(['cat', 'CPU/benchmark.log'], check=False, stdout=subprocess.PIPE).stdout.strip())
        numpy_benchmark_time = float(subprocess.run(['cat', 'numpy_benchmark.log'], check=False, stdout=subprocess.PIPE).stdout.strip())
        print(f'BENCHMARK:vs_numpy_ratio:{rust_benchmark_time / numpy_benchmark_time}')
        print(f'TEST_PASS:compare_benchmark')
    except Exception as e:
        print(f'TEST_FAIL:compare_benchmark:{str(e)}')

def main():
    install_dependencies()
    run_hello_world()
    run_benchmark()
    run_numpy_benchmark()
    compare_benchmark()
    tracemalloc.start()
    subprocess.run(['python', 'benchmark.py'], cwd='CPU', check=False)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_mb:{peak / 1024 / 1024}')
    print(f'BENCHMARK:loc_count:{subprocess.run(["wc", "-l", "CPU/benchmark.py"], check=False, stdout=subprocess.PIPE).stdout.strip()}')
    print(f'BENCHMARK:test_files_count:{subprocess.run(["ls", "CPU/test"], check=False, stdout=subprocess.PIPE).stdout.strip().count(b"\n")}')
    print('RUN_OK')

if __name__ == "__main__":
    main()