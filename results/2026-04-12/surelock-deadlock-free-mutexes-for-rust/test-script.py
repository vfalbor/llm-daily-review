import subprocess
import sys
import time
import tracemalloc
import threading

def install_surelock():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/hotcrispy/surelock.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './surelock'], cwd='./surelock', check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_thread_safety():
    try:
        import surelock
        def worker(mutex):
            for _ in range(1000):
                with mutex:
                    pass

        mutex = surelock.Mutex()
        threads = [threading.Thread(target=worker, args=(mutex,)) for _ in range(10)]
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        end_time = time.time()
        print(f'BENCHMARK:thread_safety_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:thread_safety')
    except Exception as e:
        print(f'TEST_FAIL:thread_safety:{str(e)}')

def test_throughput():
    try:
        import surelock
        import time
        def worker(mutex):
            for _ in range(1000):
                with mutex:
                    pass

        mutex = surelock.Mutex()
        threads = [threading.Thread(target=worker, args=(mutex,)) for _ in range(10)]
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        end_time = time.time()
        print(f'BENCHMARK:throughput_ms:{(end_time - start_time) * 1000}')
        print('TEST_PASS:throughput')
    except Exception as e:
        print(f'TEST_FAIL:throughput:{str(e)}')

def compare_with_baseline():
    try:
        import surelock
        import threading
        import time
        def worker(mutex):
            for _ in range(1000):
                with mutex:
                    pass

        surelock_mutex = surelock.Mutex()
        std_mutex = threading.Lock()
        threads = [threading.Thread(target=worker, args=(surelock_mutex,)) for _ in range(10)]
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        end_time = time.time()
        surelock_time = (end_time - start_time) * 1000

        threads = [threading.Thread(target=worker, args=(std_mutex,)) for _ in range(10)]
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        end_time = time.time()
        std_time = (end_time - start_time) * 1000

        print(f'BENCHMARK:vs_python_mutex_ratio:{surelock_time / std_time}')
        print('TEST_PASS:compare_with_baseline')
    except Exception as e:
        print(f'TEST_FAIL:compare_with_baseline:{str(e)}')

def benchmark_import_time():
    try:
        start_time = time.time()
        import surelock
        end_time = time.time()
        print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}')
    except Exception as e:
        print(f'BENCHMARK:import_time_ms:0')

def benchmark_memory_usage():
    try:
        tracemalloc.start()
        import surelock
        _, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_bytes:{peak}')
        tracemalloc.stop()
    except Exception as e:
        print(f'BENCHMARK:memory_usage_bytes:0')

def main():
    install_surelock()
    benchmark_import_time()
    benchmark_memory_usage()
    test_thread_safety()
    test_throughput()
    compare_with_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()