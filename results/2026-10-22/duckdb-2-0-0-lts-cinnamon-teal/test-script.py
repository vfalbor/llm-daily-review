import subprocess, sys, time, tracemalloc, sqlite3, json, traceback

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install(pkg):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def git_clone_and_editable(repo_url, name):
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo_url], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', f'./{name}'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{name}:{e}")

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        elapsed = time.time() - start
        tracemalloc.stop()
        print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.4f}")
        print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.2f}")
        return result, elapsed
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"BENCHMARK:{name}_fail:{e}")
        raise

def test_duckdb_vs_sqlite():
    try:
        import duckdb
    except Exception as e:
        print_marker(f"TEST_FAIL:import_duckdb:{e}")
        return

    try:
        # DuckDB in-memory test
        def duckdb_ops():
            con = duckdb.connect(database=':memory:')
            con.execute("CREATE TABLE t(id INTEGER, val VARCHAR)")
            con.executemany("INSERT INTO t VALUES (?, ?)", [(i, f'val{i}') for i in range(1000)])
            con.execute("SELECT * FROM t WHERE id < 10")
            return con.fetchall()

        _, duck_time = benchmark("duckdb_ops", duckdb_ops)

        # SQLite in-memory test (baseline)
        def sqlite_ops():
            con = sqlite3.connect(':memory:')
            cur = con.cursor()
            cur.execute("CREATE TABLE t(id INTEGER, val TEXT)")
            cur.executemany("INSERT INTO t VALUES (?, ?)", [(i, f'val{i}') for i in range(1000)])
            cur.execute("SELECT * FROM t WHERE id < 10")
            return cur.fetchall()

        _, sqlite_time = benchmark("sqlite_ops", sqlite_ops)

        ratio = duck_time / sqlite_time if sqlite_time != 0 else float('inf')
        print_marker(f"BENCHMARK:vs_sqlite_time_ratio:{ratio:.4f}")

        print_marker("TEST_PASS:duckdb_vs_sqlite")
    except Exception as e:
        print_marker(f"TEST_FAIL:duckdb_vs_sqlite:{e}")

def test_duckdb_simple_query():
    try:
        import duckdb
        def simple_query():
            con = duckdb.connect(database=':memory:')
            con.execute("SELECT 1")
            return con.fetchone()
        _, q_time = benchmark("simple_query", simple_query)
        print_marker("TEST_PASS:simple_query")
    except Exception as e:
        print_marker(f"TEST_FAIL:simple_query:{e}")

def test_duckdb_insert_performance():
    try:
        import duckdb
        def bulk_insert():
            con = duckdb.connect(database=':memory:')
            con.execute("CREATE TABLE t(id INTEGER, val VARCHAR)")
            data = [(i, f'val{i}') for i in range(5000)]
            con.executemany("INSERT INTO t VALUES (?, ?)", data)
            return con.execute("SELECT count(*) FROM t").fetchone()[0]
        _, ins_time = benchmark("bulk_insert", bulk_insert)
        print_marker("TEST_PASS:bulk_insert")
    except Exception as e:
        print_marker(f"TEST_FAIL:bulk_insert:{e}")

def main():
    # Install required apk packages
    install_apk('sqlite')
    install_apk('git')
    # Install duckdb via pip, fallback to source if needed
    try:
        pip_install('duckdb')
        import duckdb  # test import
    except Exception:
        print_marker("INSTALL_FAIL:duckdb:pip install failed, trying source")
        git_clone_and_editable('https://github.com/duckdb/duckdb.git', 'duckdb')
    # Run tests
    test_duckdb_vs_sqlite()
    test_duckdb_simple_query()
    test_duckdb_insert_performance()
    # Additional benchmark: count of rows inserted
    try:
        import duckdb
        con = duckdb.connect(database=':memory:')
        con.execute("CREATE TABLE t(id INTEGER)")
        con.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(2000)])
        count = con.execute("SELECT count(*) FROM t").fetchone()[0]
        print_marker(f"BENCHMARK:row_count:{count}")
    except Exception as e:
        print_marker(f"BENCHMARK:row_count_fail:{e}")

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()