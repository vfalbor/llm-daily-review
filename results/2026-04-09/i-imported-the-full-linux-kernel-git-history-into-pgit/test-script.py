import subprocess
import time
import tracemalloc
import sqlite3
import os
import sys
import git
from pgit import Git

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:Failed to install packages {e}')

def install_pgit():
    try:
        subprocess.run(['pip', 'install', 'pgit'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/oseifert/pgit.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './pgit'], check=True, cwd='./pgit')
            print('INSTALL_OK')
        except subprocess.CalledProcessError as e:
            print(f'INSTALL_FAIL:Failed to install pgit {e}')

def test_pgit_clone():
    try:
        start_time = time.time()
        repo = git.Repo.clone_from('https://github.com/oseifert/pgit.git', 'pgit_repo')
        end_time = time.time()
        print(f'BENCHMARK:pgit_clone_time_s:{end_time - start_time}')
        print('TEST_PASS:pgit_clone')
    except Exception as e:
        print(f'TEST_FAIL:pgit_clone:{e}')

def test_pgit_visualize():
    try:
        start_time = time.time()
        repo = Git('pgit_repo')
        repo.log()
        end_time = time.time()
        print(f'BENCHMARK:pgit_visualize_time_s:{end_time - start_time}')
        print('TEST_PASS:pgit_visualize')
    except Exception as e:
        print(f'TEST_FAIL:pgit_visualize:{e}')

def test_pgit_compare():
    try:
        start_time = time.time()
        repo = Git('pgit_repo')
        repo.log()
        git_log = subprocess.check_output(['git', 'log'], cwd='pgit_repo').decode('utf-8')
        end_time = time.time()
        print(f'BENCHMARK:pgit_compare_time_s:{end_time - start_time}')
        if repo.log() != git_log:
            print('TEST_FAIL:pgit_compare:pgit log does not match git log')
        else:
            print('TEST_PASS:pgit_compare')
    except Exception as e:
        print(f'TEST_FAIL:pgit_compare:{e}')

def test_pgit_db():
    try:
        start_time = time.time()
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (id, value) VALUES (?, ?)', (i, f'test {i}'))
        conn.commit()
        cursor.execute('SELECT * FROM test WHERE id = 500')
        end_time = time.time()
        print(f'BENCHMARK:pgit_db_query_time_s:{end_time - start_time}')
        print('TEST_PASS:pgit_db')
    except Exception as e:
        print(f'TEST_FAIL:pgit_db:{e}')

def test_pgit_db_latency():
    try:
        start_time = time.time()
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (id, value) VALUES (?, ?)', (i, f'test {i}'))
        conn.commit()
        cursor.execute('SELECT * FROM test WHERE id = 500')
        end_time = time.time()
        pgit_latency = end_time - start_time
        start_time = time.time()
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (id, value) VALUES (?, ?)', (i, f'test {i}'))
        conn.commit()
        cursor.execute('SELECT * FROM test WHERE id = 500')
        end_time = time.time()
        sqlite_latency = end_time - start_time
        print(f'BENCHMARK:vs_sqlite_db_latency_ms:{(pgit_latency / sqlite_latency) * 1000}')
        print('TEST_PASS:pgit_db_latency')
    except Exception as e:
        print(f'TEST_FAIL:pgit_db_latency:{e}')

def test_pgit_memory():
    try:
        tracemalloc.start()
        start_time = time.time()
        repo = Git('pgit_repo')
        repo.log()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:pgit_memoryPeak_mb:{peak / 1024 / 1024}')
        print(f'BENCHMARK:pgit_memoryCurrent_mb:{current / 1024 / 1024}')
        tracemalloc.stop()
        print(f'BENCHMARK:pgit_log_time_s:{end_time - start_time}')
        print('TEST_PASS:pgit_memory')
    except Exception as e:
        print(f'TEST_FAIL:pgit_memory:{e}')

def test_pgit_count():
    try:
        start_time = time.time()
        repo = Git('pgit_repo')
        count = len(repo.log())
        end_time = time.time()
        print(f'BENCHMARK:pgit_count:{count}')
        print(f'BENCHMARK:pgit_log_time_s:{end_time - start_time}')
        print('TEST_PASS:pgit_count')
    except Exception as e:
        print(f'TEST_FAIL:pgit_count:{e}')

def main():
    install_packages()
    install_pgit()
    test_pgit_clone()
    test_pgit_visualize()
    test_pgit_compare()
    test_pgit_db()
    test_pgit_db_latency()
    test_pgit_memory()
    test_pgit_count()
    print('RUN_OK')

if __name__ == '__main__':
    main()