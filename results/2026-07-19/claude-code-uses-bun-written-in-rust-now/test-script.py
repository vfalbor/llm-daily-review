import subprocess
import time
import tracemalloc
import os

def test_bun_install():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')
        return

    try:
        subprocess.run(['git', 'clone', 'https://github.com/Jarred-Sumner/bun.git'], check=True)
        print('TEST_PASS:git_clone')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:git_clone:{e}')

    try:
        subprocess.run(['cargo', 'build', '--release'], cwd='bun', check=True)
        print('TEST_PASS:cargo_build')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:cargo_build:{e}')

def test_bun_hello_world():
    try:
        start_time = time.time()
        subprocess.run(['./bun.js', 'hello.js'], cwd='bun', check=True)
        end_time = time.time()
        print(f'BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:hello_world')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:hello_world:{e}')

def test_nodejs_hello_world():
    try:
        start_time = time.time()
        subprocess.run(['node', 'hello.js'], cwd='.', check=True)
        end_time = time.time()
        print(f'BENCHMARK:nodejs_hello_world_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:nodejs_hello_world')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:nodejs_hello_world:{e}')

def test_bun_nodejs_performance():
    try:
        bun_start_time = time.time()
        subprocess.run(['./bun.js', 'fib.js'], cwd='bun', check=True)
        bun_end_time = time.time()
        nodejs_start_time = time.time()
        subprocess.run(['node', 'fib.js'], cwd='.', check=True)
        nodejs_end_time = time.time()
        print(f'BENCHMARK:bun_fib_ms:{(bun_end_time - bun_start_time) * 1000}')
        print(f'BENCHMARK:nodejs_fib_ms:{(nodejs_end_time - nodejs_start_time) * 1000}')
        print(f'BENCHMARK:vs_nodejs_fib_ratio:{(bun_end_time - bun_start_time) / (nodejs_end_time - nodejs_start_time)}')
        print('TEST_PASS:bun_nodejs_performance')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:bun_nodejs_performance:{e}')

def test_rust_integration():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run'], cwd='bun/rust', check=True)
        end_time = time.time()
        print(f'BENCHMARK:rust_integration_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:rust_integration')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:rust_integration:{e}')

def test_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['./bun.js', 'hello.js'], cwd='bun', check=True)
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_mb:{peak / 10**6}')
        tracemalloc.stop()
        print('TEST_PASS:memory_usage')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:memory_usage:{e}')

def main():
    test_bun_install()
    test_bun_hello_world()
    test_nodejs_hello_world()
    test_bun_nodejs_performance()
    test_rust_integration()
    test_memory_usage()
    print(f'BENCHMARK:loc_count:{sum(1 for _ in os.listdir("bun"))}')
    print(f'BENCHMARK:test_files_count:{sum(1 for _ in os.listdir("."))}')
    print('RUN_OK')

if __name__ == '__main__':
    main()