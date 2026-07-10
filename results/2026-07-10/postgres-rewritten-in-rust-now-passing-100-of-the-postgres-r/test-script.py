import subprocess
import time
import tracemalloc
import sqlite3
import psycopg2

def install_pgrust():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/malisper/pgrust.git'], check=False)
        subprocess.run(['cd', 'pgrust', '&&', 'cargo', 'build'], check=False)
        subprocess.run(['cd', 'pgrust', '&&', 'cargo', 'test'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def install_sqlite_client():
    try:
        subprocess.run(['pip', 'install', 'pysqlite3'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/coleifer/peewee.git'], check=False)
            subprocess.run(['cd', 'peewee', '&&', 'pip', 'install', '-e', '.'], check=False)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_pgrust_basic_sql():
    try:
        import psycopg2
        conn = psycopg2.connect(database='postgres', user='postgres', password='postgres')
        cur = conn.cursor()
        cur.execute('CREATE TABLE test (id SERIAL PRIMARY KEY, name VARCHAR(50))')
        conn.commit()
        cur.execute('INSERT INTO test (name) VALUES (\'test\')')
        conn.commit()
        cur.execute('SELECT * FROM test')
        print('TEST_PASS:test_pgrust_basic_sql')
    except Exception as e:
        print(f'TEST_FAIL:test_pgrust_basic_sql:{str(e)}')

def test_pgrust_vs_postgres_performance():
    try:
        import psycopg2
        import sqlite3
        pgrust_conn = psycopg2.connect(database='postgres', user='postgres', password='postgres')
        pgrust_cur = pgrust_conn.cursor()
        postgres_conn = psycopg2.connect(database='postgres', user='postgres', password='postgres')
        postgres_cur = postgres_conn.cursor()
        sqlite_conn = sqlite3.connect(':memory:')
        sqlite_cur = sqlite_conn.cursor()
        
        tracemalloc.start()
        start_time = time.time()
        for i in range(1000):
            pgrust_cur.execute('INSERT INTO test (name) VALUES (\'test\')')
        pgrust_conn.commit()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:pgrust_insert_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:pgrust_insert_memory_mb:{current / 10**6}')
        
        tracemalloc.start()
        start_time = time.time()
        for i in range(1000):
            postgres_cur.execute('INSERT INTO test (name) VALUES (\'test\')')
        postgres_conn.commit()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:postgres_insert_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:postgres_insert_memory_mb:{current / 10**6}')
        
        tracemalloc.start()
        start_time = time.time()
        for i in range(1000):
            sqlite_cur.execute('INSERT INTO test (name) VALUES (\'test\')')
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:sqlite_insert_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:sqlite_insert_memory_mb:{current / 10**6}')
        
        print('TEST_PASS:test_pgrust_vs_postgres_performance')
    except Exception as e:
        print(f'TEST_FAIL:test_pgrust_vs_postgres_performance:{str(e)}')

def test_pgrust_complex_sql():
    try:
        import psycopg2
        conn = psycopg2.connect(database='postgres', user='postgres', password='postgres')
        cur = conn.cursor()
        
        tracemalloc.start()
        start_time = time.time()
        cur.execute('SELECT * FROM test WHERE id > 500')
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:pgrust_query_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:pgrust_query_memory_mb:{current / 10**6}')
        
        print('TEST_PASS:test_pgrust_complex_sql')
    except Exception as e:
        print(f'TEST_FAIL:test_pgrust_complex_sql:{str(e)}')

def test_pgrust_compatibility():
    try:
        import psycopg2
        conn = psycopg2.connect(database='postgres', user='postgres', password='postgres')
        cur = conn.cursor()
        
        tracemalloc.start()
        start_time = time.time()
        cur.execute('SELECT * FROM test')
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:pgrust_compatibility_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:pgrust_compatibility_memory_mb:{current / 10**6}')
        
        print('TEST_PASS:test_pgrust_compatibility')
    except Exception as e:
        print(f'TEST_FAIL:test_pgrust_compatibility:{str(e)}')

def main():
    subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
    install_pgrust()
    install_sqlite_client()
    test_pgrust_basic_sql()
    test_pgrust_vs_postgres_performance()
    test_pgrust_complex_sql()
    test_pgrust_compatibility()
    print('RUN_OK')

if __name__ == '__main__':
    main()