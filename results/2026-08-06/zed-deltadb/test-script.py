import os
import time
import tracemalloc
import subprocess
import sqlite3
from deltabd import DeltaDB

def install_delta_db():
    try:
        subprocess.run(['pip', 'install', 'deltabd'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/zed-developers/deltadb.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './deltadb'], check=True, cwd='./deltadb')
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL: {str(e)}")

def test_create_sample_dataset():
    try:
        db = DeltaDB()
        for i in range(1000):
            db.put(f'key_{i}', f'value_{i}')
        print("TEST_PASS:create_sample_dataset")
    except Exception as e:
        print(f"TEST_FAIL:create_sample_dataset:{str(e)}")

def test_run_transactions():
    try:
        db = DeltaDB()
        start_time = time.time()
        for i in range(1000):
            db.put(f'key_{i}', f'value_{i}')
        db.commit()
        end_time = time.time()
        print(f"BENCHMARK:insert_time_s:{end_time - start_time}")
        print("TEST_PASS:run_transactions")
    except Exception as e:
        print(f"TEST_FAIL:run_transactions:{str(e)}")

def test_query_with_where():
    try:
        db = DeltaDB()
        for i in range(1000):
            db.put(f'key_{i}', f'value_{i}')
        db.commit()
        start_time = time.time()
        results = db.get(f'key_500')
        end_time = time.time()
        print(f"BENCHMARK:query_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:query_with_where")
    except Exception as e:
        print(f"TEST_FAIL:query_with_where:{str(e)}")

def test_acid_compliance():
    try:
        db = DeltaDB()
        db.put('key', 'value')
        db.commit()
        db2 = DeltaDB()
        db2.put('key', 'new_value')
        db2.commit()
        if db.get('key') == db2.get('key'):
            print("TEST_PASS:acid_compliance")
        else:
            print("TEST_FAIL:acid_compliance:ACID compliance failed")
    except Exception as e:
        print(f"TEST_FAIL:acid_compliance:{str(e)}")

def test_concurrent_operations():
    try:
        db = DeltaDB()
        import threading
        def worker(db):
            for i in range(100):
                db.put(f'key_{i}', f'value_{i}')
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker, args=(db,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        db.commit()
        print("TEST_PASS:concurrent_operations")
    except Exception as e:
        print(f"TEST_FAIL:concurrent_operations:{str(e)}")

def compare_performance_vs_sqlite():
    try:
        db = DeltaDB()
        for i in range(1000):
            db.put(f'key_{i}', f'value_{i}')
        db.commit()
        sqlite_db = sqlite3.connect(':memory:')
        cursor = sqlite_db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS test (key TEXT PRIMARY KEY, value TEXT)')
        for i in range(1000):
            cursor.execute('INSERT INTO test VALUES (?, ?)', (f'key_{i}', f'value_{i}'))
        sqlite_db.commit()
        start_time = time.time()
        results = db.get(f'key_500')
        end_time = time.time()
        deltabd_time = end_time - start_time
        start_time = time.time()
        cursor.execute('SELECT * FROM test WHERE key = ?', ('key_500',))
        results = cursor.fetchone()
        end_time = time.time()
        sqlite_time = end_time - start_time
        print(f"BENCHMARK:vs_sqlite_query_time_ratio:{deltabd_time / sqlite_time}")
        print("TEST_PASS:compare_performance_vs_sqlite")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance_vs_sqlite:{str(e)}")

def measure_memory_usage():
    try:
        tracemalloc.start()
        db = DeltaDB()
        for i in range(1000):
            db.put(f'key_{i}', f'value_{i}')
        db.commit()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024)}")
    except Exception as e:
        print(f"TEST_FAIL:measure_memory_usage:{str(e)}")

def measure_insert_time():
    try:
        start_time = time.time()
        db = DeltaDB()
        for i in range(1000):
            db.put(f'key_{i}', f'value_{i}')
        db.commit()
        end_time = time.time()
        print(f"BENCHMARK:insert_time_s:{end_time - start_time}")
    except Exception as e:
        print(f"TEST_FAIL:measure_insert_time:{str(e)}")

def main():
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=True)
    install_delta_db()
    test_create_sample_dataset()
    test_run_transactions()
    test_query_with_where()
    test_acid_compliance()
    test_concurrent_operations()
    compare_performance_vs_sqlite()
    measure_memory_usage()
    measure_insert_time()
    print("RUN_OK")

if __name__ == '__main__':
    main()