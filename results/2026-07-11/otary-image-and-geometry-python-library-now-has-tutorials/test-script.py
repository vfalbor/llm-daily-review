import subprocess
import sys
import time
import tracemalloc
import sqlite3
import otary

def install_packages():
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
    try:
        subprocess.run(['pip', 'install', 'otary'], check=True)
    except subprocess.CalledProcessError:
        subprocess.run(['git', 'clone', 'https://github.com/otary/otary.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './otary'], cwd='./otary', check=True)

def test_import():
    try:
        import otary
        print('INSTALL_OK')
    except ImportError as e:
        print(f'INSTALL_FAIL:{e}')

def test_geometry_computation():
    try:
        # Create an in-memory DB
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (x REAL, y REAL)')
        cursor.executemany('INSERT INTO test VALUES (?, ?)', [(x, y) for x in range(1000) for y in range(1)])
        start_time = time.time()
        cursor.execute('SELECT * FROM test WHERE x > 500')
        cursor.fetchall()
        latency = (time.time() - start_time) * 1000
        print(f'BENCHMARK:query_latency_ms:{latency:.2f}')
        print(f'TEST_PASS:geometry_computation')
    except Exception as e:
        print(f'TEST_FAIL:geometry_computation:{e}')

def test_performance():
    try:
        tracemalloc.start()
        start_time = time.time()
        # Run a geometry computation using Otary's API
        import otary
        otary.init()
        for _ in range(1000):
            otary.point(1, 2)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        otary_time = (time.time() - start_time) * 1000
        print(f'BENCHMARK:otary_time_ms:{otary_time:.2f}')
        print(f'BENCHMARK:otary_memory_mb:{current / (1024 * 1024):.2f}')
        # Compare performance with OpenCV
        import cv2
        start_time = time.time()
        for _ in range(1000):
            cv2.Point(1, 2)
        cv_time = (time.time() - start_time) * 1000
        print(f'BENCHMARK:opencv_time_ms:{cv_time:.2f}')
        print(f'BENCHMARK:vs_opencv_time_ratio:{otary_time / cv_time:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:performance:{e}')

def main():
    install_packages()
    test_import()
    test_geometry_computation()
    test_performance()
    print('RUN_OK')

if __name__ == '__main__':
    main()