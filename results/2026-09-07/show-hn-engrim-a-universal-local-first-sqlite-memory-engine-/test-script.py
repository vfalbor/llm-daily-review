#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import shutil
import tracemalloc
import sqlite3
import json
import pathlib

# Helper to print markers
def mark(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)

def install_apk(pkg):
    ok, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if ok:
        mark("INSTALL_OK")
    else:
        mark(f"INSTALL_FAIL:{err}")
    return ok

def pip_install(pkg):
    ok, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
    if ok:
        mark("INSTALL_OK")
    else:
        mark(f"INSTALL_FAIL:{err}")
    return ok

def git_clone(repo, dest):
    ok, err = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    if not ok:
        mark(f"INSTALL_FAIL:{err}")
    return ok

def measure_time(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return result, end - start

# 1. Install system packages
install_apk('sqlite')
install_apk('git')
install_apk('build-base')  # needed for possible cargo builds

# 2. Install Engrim client via pip, fallback to git+editable
engrim_installed = pip_install('engrim')
if not engrim_installed:
    repo_url = 'https://github.com/timgordontg/engrim.git'
    clone_dir = '/tmp/engrim_src'
    if os.path.isdir(clone_dir):
        shutil.rmtree(clone_dir)
    if git_clone(repo_url, clone_dir):
        # try pip install -e .
        ok, err = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=clone_dir)
        if ok:
            mark("INSTALL_OK")
            engrim_installed = True
        else:
            mark(f"INSTALL_FAIL:{err}")

# Import after installation attempts
try:
    import engrim
except Exception as e:
    engrim = None
    mark(f"INSTALL_FAIL:ImportError:{e}")

# Baseline SQLite functions
def baseline_insert(rows):
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE test(id INTEGER PRIMARY KEY, val TEXT)")
    conn.commit()
    for i in range(rows):
        cur.execute("INSERT INTO test(val) VALUES (?)", (f"value{i}",))
    conn.commit()
    conn.close()

def baseline_select(rows):
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE test(id INTEGER PRIMARY KEY, val TEXT)")
    for i in range(rows):
        cur.execute("INSERT INTO test(val) VALUES (?)", (f"value{i}",))
    conn.commit()
    start = time.time()
    cur.execute("SELECT * FROM test WHERE id > ?", (rows//2,))
    _ = cur.fetchall()
    latency = time.time() - start
    conn.close()
    return latency

# 3. Test CRUD via Engrim CLI (if available)
def test_cli_crud():
    try:
        # Engrim provides a CLI 'engrim' if installed
        db_path = "/tmp/engrim_test.db"
        # create DB and table
        run_cmd(['engrim', 'exec', db_path, 'CREATE TABLE t(id INTEGER PRIMARY KEY, name TEXT)'])
        # insert
        run_cmd(['engrim', 'exec', db_path, "INSERT INTO t(name) VALUES ('alice')"])
        # select
        result = subprocess.check_output(['engrim', 'exec', db_path, "SELECT name FROM t WHERE id=1"], text=True)
        if 'alice' not in result:
            raise AssertionError("Inserted value not found")
        # delete
        run_cmd(['engrim', 'exec', db_path, "DELETE FROM t WHERE id=1"])
        # verify deletion
        result2 = subprocess.check_output(['engrim', 'exec', db_path, "SELECT COUNT(*) FROM t"], text=True)
        if not result2.strip().endswith('0'):
            raise AssertionError("Delete failed")
        mark("TEST_PASS:cli_crud")
    except Exception as e:
        mark(f"TEST_FAIL:cli_crud:{e}")

test_cli_crud()

# 4. Benchmark insert 10k rows
def benchmark_insert(rows=10000):
    try:
        # Engrim in-memory DB via Python API if available
        if engrim:
            conn = engrim.connect(":memory:")
            cur = conn.cursor()
            cur.execute("CREATE TABLE bench(id INTEGER PRIMARY KEY, txt TEXT)")
            conn.commit()
            _, elapsed = measure_time(lambda: [cur.execute("INSERT INTO bench(txt) VALUES (?)", (f"txt{i}",)) for i in range(rows)])
            conn.commit()
            conn.close()
            mark(f"BENCHMARK:engrim_insert_ms:{elapsed*1000:.2f}")
        else:
            raise RuntimeError("Engrim module not available")
    except Exception as e:
        mark(f"TEST_FAIL:benchmark_insert:{e}")

benchmark_insert()

# 5. Benchmark SELECT WHERE and compare to SQLite baseline
def benchmark_select_compare(rows=10000):
    try:
        # Engrim select
        if not engrim:
            raise RuntimeError("Engrim not available")
        conn = engrim.connect(":memory:")
        cur = conn.cursor()
        cur.execute("CREATE TABLE bench(id INTEGER PRIMARY KEY, txt TEXT)")
        for i in range(rows):
            cur.execute("INSERT INTO bench(txt) VALUES (?)", (f"txt{i}",))
        conn.commit()
        _, engrim_latency = measure_time(lambda: cur.execute("SELECT * FROM bench WHERE id > ?", (rows//2,)).fetchall())
        conn.close()
        mark(f"BENCHMARK:engrim_select_ms:{engrim_latency*1000:.2f}")

        # SQLite baseline
        sqlite_latency = baseline_select(rows)
        mark(f"BENCHMARK:sqlite_select_ms:{sqlite_latency*1000:.2f}")

        # Ratio
        if sqlite_latency > 0:
            ratio = engrim_latency / sqlite_latency
            mark(f"BENCHMARK:vs_sqlite_select_ratio:{ratio:.3f}")
        else:
            mark("BENCHMARK:vs_sqlite_select_ratio:inf")
    except Exception as e:
        mark(f"TEST_FAIL:benchmark_select_compare:{e}")

benchmark_select_compare()

# 6. Persistence test (optional flag)
def test_persistence():
    try:
        db_file = "/tmp/engrim_persist.db"
        # create with persistence flag (assuming --persist creates file)
        run_cmd(['engrim', 'exec', '--persist', db_file, "CREATE TABLE p(id INTEGER PRIMARY KEY, val TEXT)"])
        run_cmd(['engrim', 'exec', '--persist', db_file, "INSERT INTO p(val) VALUES ('persisted')"])
        # close and reopen
        output = subprocess.check_output(['engrim', 'exec', '--persist', db_file, "SELECT val FROM p WHERE id=1"], text=True)
        if 'persisted' not in output:
            raise AssertionError("Persistence failed")
        # cleanup
        os.remove(db_file)
        mark("TEST_PASS:persistence")
    except Exception as e:
        mark(f"TEST_FAIL:persistence:{e}")

test_persistence()

# Additional generic benchmarks
def generic_benchmarks():
    # Memory usage during simple import
    tracemalloc.start()
    import math  # dummy import
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mark(f"BENCHMARK:import_memory_kb:{peak/1024:.2f}")

    # Count of .py files in repo (if cloned)
    repo_path = '/tmp/engrim_src'
    if os.path.isdir(repo_path):
        count = sum(1 for _ in pathlib.Path(repo_path).rglob('*.py'))
        mark(f"BENCHMARK:repo_py_files:{count}")

    # Simple CPU benchmark
    start = time.time()
    total = sum(i*i for i in range(100000))
    duration = time.time() - start
    mark(f"BENCHMARK:cpu_compute_ms:{duration*1000:.2f}")

generic_benchmarks()

# Ensure final marker
mark("RUN_OK")