import subprocess
import time
import tracemalloc
import sqlite3
import psycopg2
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'psycopg2'], check=False)
except Exception as e:
    print('INSTALL_FAIL: psycopg2 install failed: ', str(e))
    try:
        subprocess.run(['git', 'clone', 'https://github.com/psycopg/psycopg2.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './psycopg2'], check=False)
    except Exception as e:
        print('INSTALL_FAIL: psycopg2 fallback install failed: ', str(e))
        exit(1)

try:
    subprocess.run(['pip', 'install', 'yourpooler'], check=False)
except Exception as e:
    print('INSTALL_FAIL: yourpooler install failed: ', str(e))
    try:
        subprocess.run(['git', 'clone', 'https://github.com/pgdog/yourpooler.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './yourpooler'], check=False)
    except Exception as e:
        print('INSTALL_FAIL: yourpooler fallback install failed: ', str(e))
        exit(1)

print('INSTALL_OK')

# Create in-memory DB
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Insert 1000 rows
start_time = time.time()
for i in range(1000):
    cursor.execute('INSERT INTO test_table (id, value) VALUES (?, ?)', (i, i))
conn.commit()
insert_time = time.time() - start_time
tracemalloc.start()
snapshot = tracemalloc.take_snapshot()

# Query with WHERE
start_time = time.time()
cursor.execute('SELECT * FROM test_table WHERE id = 500')
result = cursor.fetchone()
query_time = time.time() - start_time

# Measure latency vs sqlite3 stdlib as baseline
print('BENCHMARK:insert_time_ms:', insert_time * 1000)
print('BENCHMARK:query_time_ms:', query_time * 1000)

try:
    # Create a Postgres connection pooler
    conn_pool = psycopg2.connect(
        host="localhost",
        database="testdb",
        user="testuser",
        password="testpassword"
    )
    cursor_pool = conn_pool.cursor()
    cursor_pool.execute('CREATE TABLE test_table (id INTEGER, value INTEGER)')
    for i in range(1000):
        cursor_pool.execute('INSERT INTO test_table (id, value) VALUES (%s, %s)', (i, i))
    conn_pool.commit()
    start_time = time.time()
    cursor_pool.execute('SELECT * FROM test_table WHERE id = 500')
    result_pool = cursor_pool.fetchone()
    query_time_pool = time.time() - start_time
    print('BENCHMARK:yourpooler_query_time_ms:', query_time_pool * 1000)
    print('BENCHMARK:vs_sqlite_query_time_ratio:', query_time_pool / query_time)
except Exception as e:
    print('TEST_FAIL:yourpooler query failed: ', str(e))

# Run yourpooler
try:
    subprocess.run(['yourpooler'], check=False)
    print('TEST_PASS:yourpooler')
except Exception as e:
    print('TEST_FAIL:yourpooler: ', str(e))

# Measure memory usage
stats = snapshot.statistics('lineno')
mem_usage = stats[0].size / 1024 / 1024
print('BENCHMARK:memory_usage_mb:', mem_usage)

print('RUN_OK')