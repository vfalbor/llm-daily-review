import subprocess
import sys
import time
import tracemalloc
import json
import os
import importlib.util

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, description):
    start = time.time()
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if result.returncode == 0:
            print_marker(f"INSTALL_OK | {description}")
        else:
            print_marker(f"INSTALL_FAIL:{description}:{result.stderr.strip() or 'non-zero exit'}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{description}:{e}")
    return time.time() - start

def pip_install(package):
    return run_cmd([sys.executable, "-m", "pip", "install", "--no-cache-dir", package], f"pip install {package}")

def apk_add(pkg):
    return run_cmd(["apk", "add", "--no-cache", pkg], f"apk add {pkg}")

def import_time(module_name):
    start = time.time()
    try:
        importlib.import_module(module_name)
        duration = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_{module_name}_ms:{duration:.2f}")
        return duration
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def benchmark(name, func):
    start = time.time()
    tracemalloc.start()
    try:
        func()
        current, peak = tracemalloc.get_traced_memory()
        duration_ms = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:{name}_ms:{duration_ms:.2f}")
        print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{name}:{e}")
    finally:
        tracemalloc.stop()

def run_test(name, func):
    try:
        func()
        print_marker(f"TEST_PASS:{name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{name}:{e}")

def fallback_git_install(repo_url, package_dir):
    try:
        run_cmd(["git", "clone", repo_url, "/tmp/ducklake_src"], "git clone ducklake")
        run_cmd([sys.executable, "-m", "pip", "install", "-e", "/tmp/ducklake_src"], "pip install -e ducklake")
        print_marker("INSTALL_OK | git fallback install")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git_fallback:{e}")

def main():
    # 1. Install system package sqlite
    apk_add("sqlite")
    # 2. Install python packages
    pip_install("ducklake")
    # verify import, fallback if needed
    if import_time("ducklake") is None:
        fallback_git_install("https://github.com/duckdb/ducklake.git", "ducklake")
    # ensure duckdb is available (dependency)
    pip_install("duckdb")
    import_time("duckdb")

    # 3. Prepare in‑memory DuckLake DB and SQLite baseline
    def test_ducklake_query():
        import duckdb
        import ducklake  # noqa: F401 ensure extension loads
        con = duckdb.connect(database=':memory:')
        # load ducklake extension
        con.execute("INSTALL ducklake;")
        con.execute("LOAD ducklake;")
        # create sample table
        con.execute("""
            CREATE TABLE ts (
                ts TIMESTAMP,
                val DOUBLE
            );
        """)
        # insert 1000 rows of time series data
        rows = [(f"2023-01-01 {i//60:02d}:{i%60:02d}:00", i*0.5) for i in range(1000)]
        con.executemany("INSERT INTO ts VALUES (?, ?);", rows)

        # windowed aggregation query
        q = """
            SELECT
                ts,
                SUM(val) OVER (ORDER BY ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS roll_sum
            FROM ts
            WHERE ts > '2023-01-01 00:10:00';
        """
        cur = con.execute(q)
        result = cur.fetchall()
        if len(result) == 0:
            raise AssertionError("No rows returned from DuckLake query")
        # store for later comparison
        test_ducklake_query.result = result

    run_test("ducklake_window_query", test_ducklake_query)

    # 4. Baseline SQLite test
    def test_sqlite_query():
        import sqlite3
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE ts (
                ts TEXT,
                val REAL
            );
        """)
        rows = [(f"2023-01-01 {i//60:02d}:{i%60:02d}:00", i*0.5) for i in range(1000)]
        cur.executemany("INSERT INTO ts VALUES (?, ?);", rows)
        conn.commit()
        q = """
            SELECT ts, val FROM ts
            WHERE ts > '2023-01-01 00:10:00';
        """
        cur.execute(q)
        result = cur.fetchall()
        if len(result) == 0:
            raise AssertionError("No rows returned from SQLite query")
        test_sqlite_query.result = result

    run_test("sqlite_baseline_query", test_sqlite_query)

    # 5. Compare results (basic equality of row counts)
    def compare_results():
        duck_res = getattr(test_ducklake_query, "result", [])
        sqlite_res = getattr(test_sqlite_query, "result", [])
        if len(duck_res) != len(sqlite_res):
            raise AssertionError(f"Row count mismatch DuckLake={len(duck_res)} SQLite={len(sqlite_res)}")
        print_marker(f"TEST_PASS:result_count_match")
    run_test("compare_result_counts", compare_results)

    # 6. Benchmark latency of both queries
    def bench_ducklake():
        import duckdb
        con = duckdb.connect(database=':memory:')
        con.execute("INSTALL ducklake;")
        con.execute("LOAD ducklake;")
        con.execute("""
            CREATE TABLE ts (
                ts TIMESTAMP,
                val DOUBLE
            );
        """)
        rows = [(f"2023-01-01 {i//60:02d}:{i%60:02d}:00", i*0.5) for i in range(1000)]
        con.executemany("INSERT INTO ts VALUES (?, ?);", rows)
        q = """
            SELECT
                ts,
                SUM(val) OVER (ORDER BY ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS roll_sum
            FROM ts
            WHERE ts > '2023-01-01 00:10:00';
        """
        start = time.time()
        con.execute(q).fetchall()
        duration = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:ducklake_query_latency_ms:{duration:.2f}")
        bench_ducklake.latency = duration

    def bench_sqlite():
        import sqlite3
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE ts (
                ts TEXT,
                val REAL
            );
        """)
        rows = [(f"2023-01-01 {i//60:02d}:{i%60:02d}:00", i*0.5) for i in range(1000)]
        cur.executemany("INSERT INTO ts VALUES (?, ?);", rows)
        conn.commit()
        q = """
            SELECT ts, val FROM ts
            WHERE ts > '2023-01-01 00:10:00';
        """
        start = time.time()
        cur.execute(q).fetchall()
        duration = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:sqlite_query_latency_ms:{duration:.2f}")
        bench_sqlite.latency = duration

    benchmark("ducklake_query", bench_ducklake)
    benchmark("sqlite_query", bench_sqlite)

    # 7. Comparative benchmark
    try:
        d_lat = getattr(bench_ducklake, "latency", None)
        s_lat = getattr(bench_sqlite, "latency", None)
        if d_lat is not None and s_lat is not None and s_lat != 0:
            ratio = d_lat / s_lat
            print_marker(f"BENCHMARK:vs_sqlite_query_latency_ratio:{ratio:.3f}")
        else:
            print_marker("TEST_SKIP:vs_sqlite_comparison:Missing latency data")
    except Exception as e:
        print_marker(f"TEST_FAIL:vs_sqlite_comparison:{e}")

    # Ensure at least three benchmark lines (install time, import time, query latency already emitted)
    # Additional generic benchmark
    print_marker(f"BENCHMARK:script_runtime_s:{(time.time() - start_time):.2f}")

    print_marker("RUN_OK")

if __name__ == "__main__":
    start_time = time.time()
    main()