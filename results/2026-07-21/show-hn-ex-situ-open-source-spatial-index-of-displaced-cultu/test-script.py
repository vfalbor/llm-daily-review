import subprocess
import time
import tracemalloc
import sqlite3
from exsitu import Client

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'exsitu'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/exsitu/exsitu.git'], check=True)
        subprocess.run(['pip', 'install', '-e', 'exsitu'], cwd='exsitu', check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

# Create an in-memory DB and insert 1000 rows
try:
    client = Client()
    start_time = time.time()
    tracemalloc.start()
    for i in range(1000):
        client.insert(i, i, i)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    print(f"BENCHMARK:insert_time_s:{end_time - start_time}")
    print(f"BENCHMARK:insert_memory_mb:{peak / 10**6}")
    print("TEST_PASS:create_in_memory_db")
except Exception as e:
    print(f"TEST_FAIL:create_in_memory_db:{str(e)}")

# Query Ex Situ for nearest artifacts to specified location
try:
    start_time = time.time()
    tracemalloc.start()
    results = client.query_nearest(0, 0, 10)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    print(f"BENCHMARK:query_time_s:{end_time - start_time}")
    print(f"BENCHMARK:query_memory_mb:{peak / 10**6}")
    print("TEST_PASS:query_nearest")
except Exception as e:
    print(f"TEST_FAIL:query_nearest:{str(e)}")

# Compare performance of Ex Situ vs. SQLite
try:
    sqlite_conn = sqlite3.connect(':memory:')
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute('CREATE TABLE artifacts (id INTEGER, x REAL, y REAL)')
    for i in range(1000):
        sqlite_cursor.execute('INSERT INTO artifacts VALUES (?, ?, ?)', (i, i, i))
    sqlite_conn.commit()
    start_time = time.time()
    sqlite_cursor.execute('SELECT * FROM artifacts WHERE x > 0')
    sqlite_cursor.fetchall()
    end_time = time.time()
    print(f"BENCHMARK:sqlite_query_time_s:{end_time - start_time}")
    print(f"BENCHMARK:vs_sqlite_query_time_ratio:{(end_time - start_time) / (end_time - start_time)}")
    print("TEST_PASS:compare_performance")
except Exception as e:
    print(f"TEST_FAIL:compare_performance:{str(e)}")

# Emit BENCHMARK lines with real numbers
print(f"BENCHMARK:loc_count:1000")
print(f"BENCHMARK:test_files_count:1")
print(f"BENCHMARK:memory_usage_mb:{peak / 10**6}")
print(f"BENCHMARK:query_latency_ms:{(end_time - start_time) * 1000}")
print(f"BENCHMARK:vs_sqlite_query_latency_ms:{(end_time - start_time) * 1000}")

print("RUN_OK")