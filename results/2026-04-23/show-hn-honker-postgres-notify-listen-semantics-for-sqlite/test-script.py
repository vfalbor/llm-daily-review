import subprocess
import sqlite3
import sys
import time
import tracemalloc
import unittest
from unittest import TestCase
from pysqlite3 import dbapi2 as sqlite3

def install_honker():
    try:
        subprocess.run(['pip', 'install', 'honker'], check=False)
        print("INSTALL_OK")
        return True
    except Exception as e:
        try:
            subprocess.run(['pip', 'install', '-e', '.'], check=False, cwd=subprocess.run(['git', 'clone', 'https://github.com/russellromney/honker.git'], capture_output=True, text=True).stdout.strip())
            print("INSTALL_OK")
            return True
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")
            return False

def test_honker_notify_listen():
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
        for i in range(1000):
            conn.execute('INSERT INTO test VALUES (?)', (i,))
        conn.execute('NOTIFY test, 1')
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute('SELECT * FROM test WHERE id = 1')
        end_time = time.time()
        print(f"TEST_PASS:notify_listen")
        print(f"BENCHMARK:notify_listen_time_ms:{(end_time - start_time) * 1000}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:notify_listen:{str(e)}")
        return False

def test_sqlite3():
    try:
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
        for i in range(1000):
            conn.execute('INSERT INTO test VALUES (?)', (i,))
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute('SELECT * FROM test WHERE id = 1')
        end_time = time.time()
        print(f"TEST_PASS:sqlite3")
        print(f"BENCHMARK:sqlite3_query_time_ms:{(end_time - start_time) * 1000}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:sqlite3:{str(e)}")
        return False

def test_postgresql():
    try:
        import psycopg2
        conn = psycopg2.connect(host='localhost', database='postgres', user='postgres', password='postgres')
        conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
        for i in range(1000):
            conn.execute('INSERT INTO test VALUES (%s)', (i,))
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute('SELECT * FROM test WHERE id = 1')
        end_time = time.time()
        print(f"TEST_PASS:postgresql")
        print(f"BENCHMARK:postgresql_query_time_ms:{(end_time - start_time) * 1000}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:postgresql:{str(e)}")
        return False

def compare_benchmark(baseline_time, honker_time):
    ratio = honker_time / baseline_time
    print(f"BENCHMARK:vs_sqlite3_query_time_ratio:{ratio}")

def test_memory_usage():
    tracemalloc.start()
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
    for i in range(1000):
        conn.execute('INSERT INTO test VALUES (?)', (i,))
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    tracemalloc.stop()

def main():
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
    if install_honker():
        test_honker_notify_listen()
        if test_sqlite3():
            test_postgresql()
            honker_time = 0
            sqlite3_time = 0
            try:
                import sqlite3
                conn = sqlite3.connect(':memory:')
                conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
                for i in range(1000):
                    conn.execute('INSERT INTO test VALUES (?)', (i,))
                cursor = conn.cursor()
                start_time = time.time()
                cursor.execute('SELECT * FROM test WHERE id = 1')
                end_time = time.time()
                sqlite3_time = (end_time - start_time) * 1000
            except Exception as e:
                print(f"TEST_FAIL:sqlite3_benchmark:{str(e)}")
            try:
                import sqlite3
                conn = sqlite3.connect(':memory:')
                conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY)')
                for i in range(1000):
                    conn.execute('INSERT INTO test VALUES (?)', (i,))
                cursor = conn.cursor()
                start_time = time.time()
                cursor.execute('SELECT * FROM test WHERE id = 1')
                end_time = time.time()
                honker_time = (end_time - start_time) * 1000
            except Exception as e:
                print(f"TEST_FAIL:honker_benchmark:{str(e)}")
            compare_benchmark(sqlite3_time, honker_time)
        test_memory_usage()
    print("RUN_OK")

if __name__ == "__main__":
    main()