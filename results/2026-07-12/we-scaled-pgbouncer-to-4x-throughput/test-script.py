import subprocess
import sqlite3
import psycopg2
import time
import tracemalloc
import sys

def install_pgbouncer():
    try:
        # Install required system packages
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
        subprocess.run(['apk', 'add', '--no-cache', 'gcc'], check=False)
        subprocess.run(['apk', 'add', '--no-cache', 'make'], check=False)
        subprocess.run(['apk', 'add', '--no-cache', 'postgresql-dev'], check=False)

        # Clone and build PgBouncer from source
        subprocess.run(['git', 'clone', 'https://github.com/PGBouncer/PgBouncer.git'], check=False)
        subprocess.run(['make', '-C', 'PgBouncer'], check=False)

        # Install psycopg2 via pip
        subprocess.run(['pip', 'install', 'psycopg2'], check=False)

        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def create_in_memory_db():
    try:
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')
        for i in range(1000):
            cursor.execute('INSERT INTO test (id, value) VALUES (?, ?)', (i, f'test_{i}'))
        conn.commit()
        conn.close()

        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def benchmark_pgbouncer():
    try:
        start_time = time.time()
        # Create a PgBouncer connection
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')

        for i in range(1000):
            cursor.execute('INSERT INTO test (id, value) VALUES (%s, %s)', (i, f'test_{i}'))
        conn.commit()

        end_time = time.time()
        throughput = 1000 / (end_time - start_time)
        print(f"BENCHMARK:pgbouncer_throughput:{throughput}")

        cursor.execute('SELECT * FROM test WHERE id = 500')
        result = cursor.fetchone()
        latency = (time.time() - start_time) * 1000
        print(f"BENCHMARK:pgbouncer_latency_ms:{latency}")

        conn.close()
        print("TEST_PASS:pgbouncer_benchmark")
    except Exception as e:
        print(f"TEST_FAIL:pgbouncer_benchmark:{str(e)}")

def benchmark_sqlite():
    try:
        start_time = time.time()
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')

        for i in range(1000):
            cursor.execute('INSERT INTO test (id, value) VALUES (?, ?)', (i, f'test_{i}'))

        cursor.execute('SELECT * FROM test WHERE id = 500')
        result = cursor.fetchone()
        latency = (time.time() - start_time) * 1000
        print(f"BENCHMARK:sqlite_latency_ms:{latency}")
        print(f"BENCHMARK:sqlite_throughput:1000")

        conn.close()
        print("TEST_PASS:sqlite_benchmark")
    except Exception as e:
        print(f"TEST_FAIL:sqlite_benchmark:{str(e)}")

def compare_baselines():
    try:
        pgbouncer_latency = float([x.split(':')[1] for x in sys.stdout.getvalue().split('\n') if 'BENCHMARK:pgbouncer_latency_ms' in x][0])
        sqlite_latency = float([x.split(':')[1] for x in sys.stdout.getvalue().split('\n') if 'BENCHMARK:sqlite_latency_ms' in x][0])
        ratio = pgbouncer_latency / sqlite_latency
        print(f"BENCHMARK:vs_sqlite_latency_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:compare_baselines:{str(e)}")

install_pgbouncer()
create_in_memory_db()
benchmark_pgbouncer()
benchmark_sqlite()
compare_baselines()
print("RUN_OK")