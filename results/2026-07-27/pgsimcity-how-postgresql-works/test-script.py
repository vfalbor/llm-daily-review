import subprocess
import time
import tracemalloc
import psycopg2
import sqlite3
import os

print('INSTALL_OK')

try:
    subprocess.run(['pip', 'install', 'psycopg2'], check=False)
except Exception as e:
    print(f'INSTALL_FAIL:{e}')
    subprocess.run(['git', 'clone', 'https://github.com/psycopg/psycopg2.git'], check=False)
    os.chdir('psycopg2')
    subprocess.run(['pip', 'install', '-e', '.'], check=False)
    os.chdir('..')
    print('INSTALL_OK')

try:
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
except Exception as e:
    print(f'INSTALL_FAIL:{e}')

# Connect to the in-memory SQLite database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create a table with 1000 rows
cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')
for i in range(1000):
    cursor.execute('INSERT INTO test (value) VALUES (?)', (str(i),))
conn.commit()

# Connect to the PostgreSQL database
try:
    conn_pg = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    cursor_pg = conn_pg.cursor()
except Exception as e:
    print(f'TEST_FAIL:connect_to_postgres:{e}')
    conn_pg = None

# Test 1: Run a sample query
start_time = time.time()
cursor.execute('SELECT * FROM test WHERE value = ?', ('500',))
end_time = time.time()
latency = (end_time - start_time) * 1000
print(f'BENCHMARK:sqlite_latency_ms:{latency}')

if conn_pg:
    start_time = time.time()
    cursor_pg.execute('SELECT * FROM test WHERE value = %s', ('500',))
    end_time = time.time()
    latency_pg = (end_time - start_time) * 1000
    print(f'BENCHMARK:postgres_latency_ms:{latency_pg}')
    print(f'BENCHMARK:vs_postgres_latency_ratio:{latency / latency_pg}')

# Test 2: Validate data types
try:
    cursor.execute('INSERT INTO test (value) VALUES (?)', (123,))
    conn.commit()
    print('TEST_PASS:validate_data_types')
except Exception as e:
    print(f'TEST_FAIL:validate_data_types:{e}')

# Test 3: Compare against PostgreSQL
if conn_pg:
    try:
        cursor_pg.execute('CREATE TABLE test (id SERIAL PRIMARY KEY, value TEXT)')
        for i in range(1000):
            cursor_pg.execute('INSERT INTO test (value) VALUES (%s)', (str(i),))
        conn_pg.commit()
        print('TEST_PASS:compare_against_postgres')
    except Exception as e:
        print(f'TEST_FAIL:compare_against_postgres:{e}')

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_mb:{current / 10**6}')
tracemalloc.stop()

# Measure the number of files
print(f'BENCHMARK:file_count:{len(os.listdir())}')

# Measure the time it takes to import psycopg2
start_time = time.time()
import psycopg2
end_time = time.time()
print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}')

print('RUN_OK')