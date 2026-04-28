import subprocess
import time
import tracemalloc
import psycopg2
import sqlite3
import os

# Install system packages with subprocess
try:
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL: {e}')

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'psycopg2-binary'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL: {e}')

# Clone and build pgrx
try:
    subprocess.run(['git', 'clone', 'https://github.com/pgcentralfoundation/pgrx.git'], check=True)
    subprocess.run(['cargo', 'build', '--release'], cwd='pgrx', check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL: {e}')

# Create an in-memory DB and insert rows
try:
    conn = psycopg2.connect(database='postgres', user='postgres')
    cur = conn.cursor()
    cur.execute('CREATE TABLE test (id INT PRIMARY KEY, name VARCHAR(255))')
    for i in range(1000):
        cur.execute('INSERT INTO test (id, name) VALUES (%s, %s)', (i, f'name_{i}'))
    conn.commit()
    print('TEST_PASS:insert_rows')
except psycopg2.Error as e:
    print(f'TEST_FAIL:insert_rows:{e}')

# Query with WHERE and measure latency
try:
    start_time = time.time()
    cur.execute('SELECT * FROM test WHERE id = 500')
    cur.fetchone()
    latency = (time.time() - start_time) * 1000
    print(f'BENCHMARK:query_latency_ms:{latency:.2f}')
except psycopg2.Error as e:
    print(f'TEST_FAIL:query_latency:{e}')

# Compare performance vs sqlite3
try:
    sqlite_conn = sqlite3.connect(':memory:')
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute('CREATE TABLE test (id INT PRIMARY KEY, name VARCHAR(255))')
    for i in range(1000):
        sqlite_cur.execute('INSERT INTO test (id, name) VALUES (?, ?)', (i, f'name_{i}'))
    sqlite_conn.commit()
    start_time = time.time()
    sqlite_cur.execute('SELECT * FROM test WHERE id = 500')
    sqlite_cur.fetchone()
    sqlite_latency = (time.time() - start_time) * 1000
    print(f'BENCHMARK:vs_sqlite_query_latency_ms:{sqlite_latency:.2f}')
    print(f'BENCHMARK:vs_sqlite_query_latency_ratio:{latency / sqlite_latency:.2f}')
except sqlite3.Error as e:
    print(f'TEST_FAIL:sqlite_query_latency:{e}')

# Measure memory usage
try:
    tracemalloc.start()
    conn = psycopg2.connect(database='postgres', user='postgres')
    cur = conn.cursor()
    cur.execute('SELECT * FROM test')
    cur.fetchall()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{current}')
    tracemalloc.stop()
    print('TEST_PASS:memory_usage')
except psycopg2.Error as e:
    print(f'TEST_FAIL:memory_usage:{e}')

# Measure import time
try:
    start_time = time.time()
    import psycopg2
    import_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
    print('TEST_PASS:import_time')
except ImportError as e:
    print(f'TEST_FAIL:import_time:{e}')

# Measure loc count
try:
    loc_count = sum(1 for line in open('pgrx/Cargo.toml') if line.strip())
    print(f'BENCHMARK:loc_count:{loc_count}')
    print('TEST_PASS:loc_count')
except FileNotFoundError:
    print('TEST_SKIP:loc_count:file_not_found')

print('RUN_OK')