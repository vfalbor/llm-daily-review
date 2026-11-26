import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib, shlex, signal, threading, socket, sqlite3

# Helper to print markers
def emit(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk(pkg):
    res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
    if res and res.returncode == 0:
        emit(f"INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else str(e))
        emit(f"INSTALL_FAIL:{reason}")

def install_python_pkg(pkg):
    res = run_cmd([sys.executable, '-m', 'pip', 'install', pkg], check=False)
    if res and res.returncode == 0:
        emit(f"INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else "pip install failed")
        emit(f"INSTALL_FAIL:{reason}")

def download_minipg():
    url = "https://github.com/progrium/minipg/releases/download/v0.3.2/minipg-linux-amd64"
    binary_path = "/tmp/minipg"
    try:
        res = run_cmd(['wget', '-q', '-O', binary_path, url], check=False)
        if res and res.returncode == 0:
            os.chmod(binary_path, 0o755)
            emit("INSTALL_OK")
            return binary_path
        else:
            emit(f"INSTALL_FAIL:wget failed")
            return None
    except Exception as e:
        emit(f"INSTALL_FAIL:{e}")
        return None

def start_minipg(binary_path):
    # start on random free port
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    proc = subprocess.Popen([binary_path, f'--port={port}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # give it a moment to start
    time.sleep(1)
    return proc, port

def stop_process(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

def benchmark(func, name):
    tracemalloc.start()
    start = time.time()
    try:
        func()
        elapsed = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        emit(f"BENCHMARK:{name}_ms:{elapsed*1000:.2f}")
        emit(f"BENCHMARK:{name}_mem_kb:{peak/1024:.2f}")
        return elapsed
    except Exception as e:
        tracemalloc.stop()
        emit(f"TEST_FAIL:{name}:{e}")
        return None

def run_tests():
    # 1. Install required apk packages
    try:
        install_apk('sqlite')
        install_apk('wget')
    except Exception as e:
        emit(f"INSTALL_FAIL:{e}")

    # 2. Install Python client (psycopg2-binary)
    try:
        install_python_pkg('psycopg2-binary')
    except Exception as e:
        emit(f"INSTALL_FAIL:{e}")

    # 3. Download minipg binary
    binary = download_minipg()
    if not binary:
        emit("TEST_SKIP:minipg_download:binary not available")
        return

    # 4. Start minipg instance
    proc, port = start_minipg(binary)
    if not proc or proc.poll() is not None:
        emit("TEST_FAIL:minipg_start:process did not start")
        return

    # Ensure cleanup
    def cleanup():
        stop_process(proc)
    threading.Thread(target=lambda: (time.sleep(30), cleanup())).start()

    # 5. Connect using psycopg2
    import psycopg2
    conn = None
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=port, user='postgres', password='', database='postgres')
        conn.autocommit = True
        cur = conn.cursor()
        emit("TEST_PASS:connect")
    except Exception as e:
        emit(f"TEST_FAIL:connect:{e}")
        cleanup()
        return

    # Helper to execute SQL
    def exec_sql(sql, params=None):
        cur.execute(sql, params)

    # 6. Create table
    try:
        exec_sql("DROP TABLE IF EXISTS test")
        exec_sql("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)")
        emit("TEST_PASS:create_table")
    except Exception as e:
        emit(f"TEST_FAIL:create_table:{e}")

    # 7. Insert 1000 rows benchmark
    def insert_rows():
        for i in range(1000):
            exec_sql("INSERT INTO test (name, value) VALUES (%s, %s)", (f'name{i}', i))
    insert_time = benchmark(insert_rows, "write_latency")
    if insert_time is not None:
        emit("TEST_PASS:insert_rows")
    else:
        emit("TEST_FAIL:insert_rows:benchmark error")

    # 8. Query with WHERE benchmark
    def select_query():
        exec_sql("SELECT * FROM test WHERE value % 2 = 0")
        cur.fetchall()
    select_time = benchmark(select_query, "read_latency")
    if select_time is not None:
        emit("TEST_PASS:select_query")
    else:
        emit("TEST_FAIL:select_query:benchmark error")

    # 9. Baseline with sqlite3
    sqlite_conn = sqlite3.connect(":memory:")
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)")
    sqlite_conn.commit()
    def sqlite_insert():
        for i in range(1000):
            sqlite_cur.execute("INSERT INTO test (name, value) VALUES (?,?)", (f'name{i}', i))
        sqlite_conn.commit()
    sqlite_insert_time = benchmark(sqlite_insert, "sqlite_write_latency")
    def sqlite_select():
        sqlite_cur.execute("SELECT * FROM test WHERE value % 2 = 0")
        sqlite_cur.fetchall()
    sqlite_select_time = benchmark(sqlite_select, "sqlite_read_latency")

    # 10. Compare benchmarks
    if insert_time and sqlite_insert_time:
        ratio = insert_time / sqlite_insert_time
        emit(f"BENCHMARK:vs_sqlite_write_latency_ratio:{ratio:.2f}")
    if select_time and sqlite_select_time:
        ratio = select_time / sqlite_select_time
        emit(f"BENCHMARK:vs_sqlite_read_latency_ratio:{ratio:.2f}")

    # Cleanup
    if conn:
        conn.close()
    sqlite_conn.close()
    cleanup()

run_tests()
emit("RUN_OK")