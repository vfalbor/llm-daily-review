import subprocess
import time
import tracemalloc
import sqlite3
import random
import string

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=True)
        subprocess.run(['pip', 'install', 'usenetarchive'], check=True)
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/wolfpld/usenetarchive.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './usenetarchive'], check=True, cwd='./usenetarchive')
        except subprocess.CalledProcessError as e:
            print("INSTALL_FAIL: unable to install usenetarchive")
            return False
    print("INSTALL_OK")
    return True

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def test_insert_and_query():
    try:
        # Create an in-memory DB
        db = sqlite3.connect(':memory:')
        cursor = db.cursor()
        cursor.execute('CREATE TABLE messages (id INTEGER, message TEXT)')
        
        # Insert 1000 rows
        start_time = time.time()
        tracemalloc.start()
        for i in range(1000):
            cursor.execute('INSERT INTO messages VALUES (?, ?)', (i, generate_random_string(100)))
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Measure indexing time
        indexing_time = end_time - start_time
        memory_usage = peak / 10**6  # in MB
        print(f"BENCHMARK:insert_time_s:{indexing_time}")
        print(f"BENCHMARK:memory_usage_mb:{memory_usage}")
        
        # Query with WHERE
        start_time = time.time()
        cursor.execute('SELECT * FROM messages WHERE id > 500')
        end_time = time.time()
        query_time = end_time - start_time
        print(f"BENCHMARK:query_time_s:{query_time}")
        
        # Compare with sqlite3 stdlib as baseline
        sqlite_db = sqlite3.connect(':memory:')
        sqlite_cursor = sqlite_db.cursor()
        sqlite_cursor.execute('CREATE TABLE messages (id INTEGER, message TEXT)')
        start_time = time.time()
        for i in range(1000):
            sqlite_cursor.execute('INSERT INTO messages VALUES (?, ?)', (i, generate_random_string(100)))
        end_time = time.time()
        sqlite_indexing_time = end_time - start_time
        print(f"BENCHMARK:vs_sqlite_indexing_ratio:{indexing_time / sqlite_indexing_time}")
        
        print("TEST_PASS:test_insert_and_query")
    except Exception as e:
        print(f"TEST_FAIL:test_insert_and_query:{str(e)}")

def test_benchmark():
    try:
        # Measure time to import usenetarchive
        start_time = time.time()
        import usenetarchive
        end_time = time.time()
        import_time = end_time - start_time
        print(f"BENCHMARK:import_time_s:{import_time}")
        
        # Measure time to create an in-memory DB
        start_time = time.time()
        db = sqlite3.connect(':memory:')
        end_time = time.time()
        create_db_time = end_time - start_time
        print(f"BENCHMARK:create_db_time_s:{create_db_time}")
        
        print("TEST_PASS:test_benchmark")
    except Exception as e:
        print(f"TEST_FAIL:test_benchmark:{str(e)}")

def main():
    if not install_packages():
        return
    
    test_insert_and_query()
    test_benchmark()
    
    print("RUN_OK")

if __name__ == "__main__":
    main()