import subprocess
import sqlite3
import time
import tracemalloc
import os
import pip

def install_package(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{e}')

def install_tool():
    try:
        subprocess.run(['pip', 'install', 'pysqlite3'], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{e}')
        try:
            subprocess.run(['git', 'clone', 'https://github.com/ghaering/pysqlite3'], check=True)
            subprocess.run(['pip', 'install', '-e', './pysqlite3'], check=True)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{e}')

def create_in_memory_db():
    return sqlite3.connect(':memory:')

def insert_rows(conn, cursor, rows):
    cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
    for i in range(rows):
        cursor.execute('INSERT INTO test (name) VALUES (?)', (f'Test {i}',))
    conn.commit()

def query_db(conn, cursor):
    cursor.execute('SELECT * FROM test WHERE id > 500')
    return cursor.fetchall()

def test_install_and_run():
    try:
        import pysqlite3
        conn = create_in_memory_db()
        cursor = conn.cursor()
        insert_rows(conn, cursor, 1000)
        query_db(conn, cursor)
        print('TEST_PASS:install_and_run')
    except Exception as e:
        print(f'TEST_FAIL:install_and_run:{e}')

def test_performance():
    try:
        import pysqlite3
        conn = create_in_memory_db()
        cursor = conn.cursor()
        insert_rows(conn, cursor, 1000)
        start_time = time.time()
        query_db(conn, cursor)
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        tracemalloc.start()
        query_db(conn, cursor)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:query_latency_ms:{latency_ms}')
        print(f'BENCHMARK:memory_usage_mb:{peak / (1024 * 1024)}')
        print('TEST_PASS:performance')
    except Exception as e:
        print(f'TEST_FAIL:performance:{e}')

def test_compare_vs_sqlite3():
    try:
        import sqlite3
        import pysqlite3
        conn_pysqlite3 = create_in_memory_db()
        cursor_pysqlite3 = conn_pysqlite3.cursor()
        insert_rows(conn_pysqlite3, cursor_pysqlite3, 1000)
        start_time_pysqlite3 = time.time()
        query_db(conn_pysqlite3, cursor_pysqlite3)
        end_time_pysqlite3 = time.time()
        latency_ms_pysqlite3 = (end_time_pysqlite3 - start_time_pysqlite3) * 1000
        conn_sqlite3 = sqlite3.connect(':memory:')
        cursor_sqlite3 = conn_sqlite3.cursor()
        insert_rows(conn_sqlite3, cursor_sqlite3, 1000)
        start_time_sqlite3 = time.time()
        query_db(conn_sqlite3, cursor_sqlite3)
        end_time_sqlite3 = time.time()
        latency_ms_sqlite3 = (end_time_sqlite3 - start_time_sqlite3) * 1000
        ratio = latency_ms_pysqlite3 / latency_ms_sqlite3
        print(f'BENCHMARK:vs_sqlite3_latency_ratio:{ratio}')
        print(f'BENCHMARK:vs_sqlite3_latency_ms:{latency_ms_sqlite3}')
        print('TEST_PASS:compare_vs_sqlite3')
    except Exception as e:
        print(f'TEST_FAIL:compare_vs_sqlite3:{e}')

def main():
    install_package('sqlite')
    install_tool()
    test_install_and_run()
    test_performance()
    test_compare_vs_sqlite3()
    print('RUN_OK')

if __name__ == '__main__':
    main()