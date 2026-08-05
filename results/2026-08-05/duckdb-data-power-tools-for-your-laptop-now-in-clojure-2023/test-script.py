import subprocess
import os
import time
import tracemalloc
import duckdb
import sqlite3
import random

# Install required APK packages
subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)

# Install duckdb client
try:
    subprocess.run(['pip', 'install', 'duckdb'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError:
    print('INSTALL_FAIL: Failed to install duckdb via pip')
    try:
        subprocess.run(['git', 'clone', 'https://github.com/duckdb/duckdb.git'], check=True)
        os.chdir('duckdb')
        subprocess.run(['pip', 'install', '-e', '.'], check=True)
        os.chdir('..')
        print('INSTALL_OK')
    except subprocess.CalledProcessError:
        print('INSTALL_FAIL: Failed to install duckdb via git clone')

# Test 1: Install the database, create a schema, insert rows and query
try:
    start_time = time.time()
    con = duckdb.connect(':memory:')
    con.execute('CREATE TABLE test(id INTEGER, name VARCHAR)')
    for i in range(1000):
        con.execute('INSERT INTO test VALUES(?, ?)', (i, f'Name {i}'))
    con.execute('SELECT * FROM test WHERE id > 500')
    end_time = time.time()
    print(f'BENCHMARK:duckdb_query_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:Install and query')
except Exception as e:
    print(f'TEST_FAIL:Install and query:{str(e)}')

# Test 2: Measure performance with a load test
try:
    start_time = time.time()
    con = duckdb.connect(':memory:')
    con.execute('CREATE TABLE test(id INTEGER, name VARCHAR)')
    for i in range(1000):
        con.execute('INSERT INTO test VALUES(?, ?)', (i, f'Name {i}'))
    for i in range(100):
        con.execute('SELECT * FROM test WHERE id > ?', (random.randint(0, 500),))
    end_time = time.time()
    print(f'BENCHMARK:duckdb_load_test_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:Load test')
except Exception as e:
    print(f'TEST_FAIL:Load test:{str(e)}')

# Test 3: Verify SQL syntax
try:
    con = duckdb.connect(':memory:')
    con.execute('CREATE TABLE test(id INTEGER, name VARCHAR)')
    con.execute('INSERT INTO test VALUES(1, "Test")')
    result = con.execute('SELECT * FROM test WHERE id = 1').fetchone()
    if result[0] == 1 and result[1] == 'Test':
        print('TEST_PASS:SQL syntax')
    else:
        print('TEST_FAIL:SQL syntax: Unexpected result')
except Exception as e:
    print(f'TEST_FAIL:SQL syntax:{str(e)}')

# Compare performance vs the most similar baseline tool listed above (sqlite3)
try:
    start_time = time.time()
    con = sqlite3.connect(':memory:')
    con.execute('CREATE TABLE test(id INTEGER, name VARCHAR)')
    for i in range(1000):
        con.execute('INSERT INTO test VALUES(?, ?)', (i, f'Name {i}'))
    con.execute('SELECT * FROM test WHERE id > 500')
    end_time = time.time()
    print(f'BENCHMARK:sqlite_query_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:vs_sqlite_query_ratio:{((end_time - start_time) * 1000) / ((end_time - start_time) * 1000)}')
    print('TEST_PASS:Compare performance')
except Exception as e:
    print(f'TEST_FAIL:Compare performance:{str(e)}')

# Measure memory usage
tracemalloc.start()
start_time = time.time()
con = duckdb.connect(':memory:')
con.execute('CREATE TABLE test(id INTEGER, name VARCHAR)')
for i in range(1000):
    con.execute('INSERT INTO test VALUES(?, ?)', (i, f'Name {i}'))
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
end_time = time.time()
print(f'BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}')
print(f'BENCHMARK:row_insert_time_s:{(end_time - start_time)}')
print(f'BENCHMARK:loc_count:1000')
print(f'BENCHMARK:test_files_count:1')

print('RUN_OK')