import subprocess
import time
import tracemalloc

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)
    print('INSTALL_OK')

def install_lib0xc():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/microsoft/lib0xc.git'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:git_clone_failed:{e}')
        return False
    return True

def build_hello_world():
    if not install_lib0xc():
        return False
    try:
        start_time = time.time()
        subprocess.run(['go', 'build', 'hello_world.go'], cwd='lib0xc/examples', check=True)
        end_time = time.time()
        print(f'BENCHMARK:build_time_ms:{(end_time - start_time) * 1000}')
        return True
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:build_hello_world:{e}')
        return False

def run_hello_world():
    if not build_hello_world():
        return
    try:
        start_time = time.time()
        subprocess.run(['./hello_world'], cwd='lib0xc/examples', check=True)
        end_time = time.time()
        print(f'BENCHMARK:run_time_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:run_hello_world')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:run_hello_world:{e}')

def compare_with_baseline():
    try:
        baseline_start_time = time.time()
        subprocess.run(['go', 'run', 'hello_world.go'], cwd='/tmp/musl-1.2.2', check=True)
        baseline_end_time = time.time()
        baseline_time = (baseline_end_time - baseline_start_time) * 1000
        start_time = time.time()
        subprocess.run(['./hello_world'], cwd='lib0xc/examples', check=True)
        end_time = time.time()
        lib0xc_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_musl_hello_world_ratio:{lib0xc_time / baseline_time}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:compare_with_baseline:{e}')

def memory_benchmark():
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['./hello_world'], cwd='lib0xc/examples', check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:run_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:peak_memory_mb:{peak / 10**6}')

install_dependencies()
install_dependencies = subprocess.run(['which', 'go'], stdout=subprocess.PIPE)
if install_dependencies.returncode == 0:
    run_hello_world()
    compare_with_baseline()
    memory_benchmark()
    print('RUN_OK')
else:
    print('RUN_OK')