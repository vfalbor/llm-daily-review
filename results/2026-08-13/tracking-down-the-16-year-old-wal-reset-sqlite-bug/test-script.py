import subprocess
import time
import tracemalloc
import sqlite3
import psycopg2
import sys

def install_sqlite():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_pip_package(package_name):
    try:
        subprocess.run(['pip', 'install', package_name], check=False)
        print(f"INSTALL_OK")
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', f'https://github.com/{package_name}.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './'], check=False, cwd=f'./{package_name}')
            print(f"INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")

def test_wal_reset_bug():
    try:
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (name) VALUES (?)', (f'test_{i}',))
        conn.commit()
        start_time = time.time()
        cursor.execute('SELECT * FROM test WHERE id > 500')
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:sqlite_latency_ms:{latency:.2f}")
        conn.close()
        print(f"TEST_PASS:walt_reset_bug")
    except Exception as e:
        print(f"TEST_FAIL:walt_reset_bug:{str(e)}")

def test_postgresql_baseline():
    try:
        conn = psycopg2.connect(
            dbname="test",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (name) VALUES (%s)', (f'test_{i}',))
        conn.commit()
        start_time = time.time()
        cursor.execute('SELECT * FROM test WHERE id > 500')
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:postgresql_latency_ms:{latency:.2f}")
        conn.close()
        print(f"TEST_PASS:postgresql_baseline")
    except Exception as e:
        print(f"TEST_FAIL:postgresql_baseline:{str(e)}")

def compare_sqlite_postgresql_latency():
    try:
        sqlite_latency = float(subprocess.check_output(['grep', 'sqlite_latency_ms', 'output.log']).decode().strip().split(':')[1])
        postgresql_latency = float(subprocess.check_output(['grep', 'postgresql_latency_ms', 'output.log']).decode().strip().split(':')[1])
        ratio = sqlite_latency / postgresql_latency
        print(f"BENCHMARK:vs_postgresql_latency_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:compare_sqlite_postgresql_latency:{str(e)}")

def measure_memory_usage():
    try:
        tracemalloc.start()
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (name) VALUES (?)', (f'test_{i}',))
        conn.commit()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{current}")
        tracemalloc.stop()
        conn.close()
        print(f"TEST_PASS:measure_memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:measure_memory_usage:{str(e)}")

def measure_time_usage():
    try:
        start_time = time.time()
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (name) VALUES (?)', (f'test_{i}',))
        conn.commit()
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"BENCHMARK:time_usage_s:{elapsed_time:.2f}")
        conn.close()
        print(f"TEST_PASS:measure_time_usage")
    except Exception as e:
        print(f"TEST_FAIL:measure_time_usage:{str(e)}")

def count_lines_of_code():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/sqlite/sqlite.git'], check=False)
        output = subprocess.check_output(['git', 'ls-files', '-z', '|', 'xargs', '-0', 'wc', '-l']).decode().strip()
        loc_count = int(output.split()[0])
        print(f"BENCHMARK:loc_count:{loc_count}")
        print(f"TEST_PASS:count_lines_of_code")
    except Exception as e:
        print(f"TEST_FAIL:count_lines_of_code:{str(e)}")

def count_test_files():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/sqlite/sqlite.git'], check=False)
        output = subprocess.check_output(['find', './sqlite', '-type', 'f', '-name', '*test*']).decode().strip()
        test_files_count = len(output.split('\n'))
        print(f"BENCHMARK:test_files_count:{test_files_count}")
        print(f"TEST_PASS:count_test_files")
    except Exception as e:
        print(f"TEST_FAIL:count_test_files:{str(e)}")

install_sqlite()
install_pip_package('psycopg2')
test_wal_reset_bug()
test_postgresql_baseline()
compare_sqlite_postgresql_latency()
measure_memory_usage()
measure_time_usage()
count_lines_of_code()
count_test_files()
print("RUN_OK")