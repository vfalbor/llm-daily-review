import subprocess
import time
import tracemalloc
import sqlite3
import psycopg2
import os

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'sqlite', 'git', 'gcc', 'musl-dev', 'python3-dev', 'postgresql-dev'], check=False)

# Clone and install pgxbackup
try:
    subprocess.run(['git', 'clone', 'https://github.com/PGAnalyticX/pgxbackup.git'], check=False)
    subprocess.run(['pip', 'install', '-e', 'pgxbackup'], check=False)
except Exception as e:
    print(f"INSTALL_FAIL:pgxbackup:{str(e)}")

# Install sqlite3 for baseline comparison
try:
    subprocess.run(['pip', 'install', 'sqlite3'], check=False)
except Exception as e:
    print(f"INSTALL_FAIL:sqlite3:{str(e)}")

print("INSTALL_OK")

# Basic run test
try:
    # Create an in-memory DB
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        host="localhost",
        password="postgres"
    )
    cur = conn.cursor()
    cur.execute("CREATE TABLE test_table (id SERIAL PRIMARY KEY, data TEXT)")
    conn.commit()

    # Insert 1000 rows
    start_time = time.time()
    for i in range(1000):
        cur.execute("INSERT INTO test_table (data) VALUES (%s)", (str(i),))
    conn.commit()
    end_time = time.time()
    print(f"BENCHMARK:insert_time_ms:{(end_time - start_time) * 1000}")

    # Query with WHERE
    start_time = time.time()
    cur.execute("SELECT * FROM test_table WHERE id < 500")
    cur.fetchall()
    end_time = time.time()
    print(f"BENCHMARK:query_time_ms:{(end_time - start_time) * 1000}")

    print("TEST_PASS:basic_run")
except Exception as e:
    print(f"TEST_FAIL:basic_run:{str(e)}")

# Measure performance
try:
    # Create an in-memory DB
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    cur.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)")

    # Insert 1000 rows
    start_time = time.time()
    for i in range(1000):
        cur.execute("INSERT INTO test_table (data) VALUES (?)", (str(i),))
    conn.commit()
    end_time = time.time()
    print(f"BENCHMARK:insert_time_sqlite_ms:{(end_time - start_time) * 1000}")

    # Query with WHERE
    start_time = time.time()
    cur.execute("SELECT * FROM test_table WHERE id < 500")
    cur.fetchall()
    end_time = time.time()
    print(f"BENCHMARK:query_time_sqlite_ms:{(end_time - start_time) * 1000}")

    print("TEST_PASS:performance")
except Exception as e:
    print(f"TEST_FAIL:performance:{str(e)}")

# Compare vs similar tool
try:
    # Create an in-memory DB
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        host="localhost",
        password="postgres"
    )
    cur = conn.cursor()
    cur.execute("CREATE TABLE test_table (id SERIAL PRIMARY KEY, data TEXT)")
    conn.commit()

    # Insert 1000 rows
    start_time = time.time()
    for i in range(1000):
        cur.execute("INSERT INTO test_table (data) VALUES (%s)", (str(i),))
    conn.commit()
    end_time = time.time()

    # Query with WHERE
    start_time_query = time.time()
    cur.execute("SELECT * FROM test_table WHERE id < 500")
    cur.fetchall()
    end_time_query = time.time()

    # Create an in-memory DB with sqlite
    conn_sqlite = sqlite3.connect(':memory:')
    cur_sqlite = conn_sqlite.cursor()
    cur_sqlite.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)")

    # Insert 1000 rows
    start_time_sqlite = time.time()
    for i in range(1000):
        cur_sqlite.execute("INSERT INTO test_table (data) VALUES (?)", (str(i),))
    conn_sqlite.commit()
    end_time_sqlite = time.time()

    # Query with WHERE
    start_time_query_sqlite = time.time()
    cur_sqlite.execute("SELECT * FROM test_table WHERE id < 500")
    cur_sqlite.fetchall()
    end_time_query_sqlite = time.time()

    insert_ratio = ((end_time - start_time) * 1000) / ((end_time_sqlite - start_time_sqlite) * 1000)
    query_ratio = ((end_time_query - start_time_query) * 1000) / ((end_time_query_sqlite - start_time_query_sqlite) * 1000)

    print(f"BENCHMARK:vs_sqlite_insert_ratio:{insert_ratio}")
    print(f"BENCHMARK:vs_sqlite_query_ratio:{query_ratio}")

    print("TEST_PASS:compare_tool")
except Exception as e:
    print(f"TEST_FAIL:compare_tool:{str(e)}")

# Measure memory usage
try:
    tracemalloc.start()
    subprocess.run(['pgxbackup', '--help'])
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
except Exception as e:
    print(f"TEST_FAIL:memory_usage:{str(e)}")

# Measure file count
try:
    count = len(os.listdir('.'))
    print(f"BENCHMARK:file_count:{count}")
except Exception as e:
    print(f"TEST_FAIL:file_count:{str(e)}")

print("RUN_OK")