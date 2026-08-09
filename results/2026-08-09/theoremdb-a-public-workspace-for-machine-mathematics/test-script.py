import subprocess
import time
import tracemalloc
import sqlite3
import theoremdb

# Install APK packages
subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)

# Install theoremdb client
try:
    subprocess.run(['pip', 'install', 'theoremdb'], check=False)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL: theoremdb installation via pip failed")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/theoremdb/theoremdb.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './theoremdb'], check=False)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL: theoremdb installation via git and pip failed")

# Create an in-memory TheoremDB database
try:
    db = theoremdb.Database()
except Exception as e:
    print(f"TEST_FAIL: create_database:{str(e)}")
else:
    print("TEST_PASS:create_database")

# Insert 1000 rows into the database
start_time = time.time()
try:
    for i in range(1000):
        db.insert(f"fact_{i}", f"value_{i}")
except Exception as e:
    print(f"TEST_FAIL:insert_rows:{str(e)}")
else:
    print("TEST_PASS:insert_rows")
    end_time = time.time()
    print(f"BENCHMARK:insert_time_ms:{(end_time - start_time) * 1000:.2f}")

# Query the database with WHERE clause
start_time = time.time()
try:
    results = db.query(f"fact_500 LIKE '%value%'")
except Exception as e:
    print(f"TEST_FAIL:query_database:{str(e)}")
else:
    print("TEST_PASS:query_database")
    end_time = time.time()
    print(f"BENCHMARK:query_latency_ms:{(end_time - start_time) * 1000:.2f}")

# Measure memory usage
tracemalloc.start()
db.query(f"fact_500 LIKE '%value%'")
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024):.2f}")
tracemalloc.stop()

# Compare performance with sqlite3 as baseline
try:
    sqlite_conn = sqlite3.connect(':memory:')
    cursor = sqlite_conn.cursor()
    cursor.execute('CREATE TABLE facts (fact TEXT, value TEXT)')
    for i in range(1000):
        cursor.execute('INSERT INTO facts VALUES (?, ?)', (f"fact_{i}", f"value_{i}"))
    sqlite_conn.commit()
    start_time = time.time()
    cursor.execute('SELECT * FROM facts WHERE fact LIKE "%fact_500%"')
    cursor.fetchall()
    end_time = time.time()
    print(f"BENCHMARK:vs_sqlite_query_latency_ms:{(end_time - start_time) * 1000:.2f}")
    baseline_time = (end_time - start_time) * 1000
    theoremdb_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_sqlite_query_latency_ratio:{theoremdb_time / baseline_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:compare_with_sqlite:{str(e)}")

print("RUN_OK")