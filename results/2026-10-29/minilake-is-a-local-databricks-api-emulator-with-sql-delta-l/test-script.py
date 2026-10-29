import subprocess, sys, os, time, json, socket, threading, tracemalloc, urllib.request, urllib.error, urllib.parse

# Helper to print markers
def print_marker(msg):
    sys.stdout.flush()
    print(msg)

# Benchmark collector
benchmarks = []

def add_benchmark(name, value):
    benchmarks.append((name, value))
    print_marker(f"BENCHMARK:{name}:{value}")

# 1. Install system packages
def install_system():
    start = time.time()
    try:
        subprocess.run(['apk','add','--no-cache','sqlite','git','python3-dev','build-base'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    add_benchmark("install_time_s", round(time.time() - start, 2))

install_system()

# 2. Install Python dependencies (requests)
def install_deps():
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'requests'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    add_benchmark("pip_install_time_s", round(time.time() - start, 2))

install_deps()

# 3. Clone repository and install minilake
REPO_URL = "https://github.com/dmux/minilake.git"
REPO_DIR = "/tmp/minilake"

def clone_and_install():
    start = time.time()
    try:
        if os.path.isdir(REPO_DIR):
            subprocess.run(['rm','-rf',REPO_DIR], check=False)
        subprocess.run(['git','clone','--depth','1',REPO_URL, REPO_DIR], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # try pip install
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', REPO_DIR], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    add_benchmark("clone_install_time_s", round(time.time() - start, 2))

clone_and_install()

# 4. Start minilake server
server_process = None
def start_server():
    global server_process
    start = time.time()
    try:
        server_process = subprocess.Popen([sys.executable, '-m', 'minilake', 'serve'], cwd=REPO_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # wait for port 8080 to be open
        timeout = 30
        start_wait = time.time()
        while time.time() - start_wait < timeout:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.settimeout(1)
                    s.connect(('127.0.0.1', 8080))
                    break
                except OSError:
                    time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start on port 8080")
        print_marker("TEST_PASS:server_start")
    except Exception as e:
        print_marker(f"TEST_FAIL:server_start:{e}")
    add_benchmark("server_start_time_s", round(time.time() - start, 2))

start_server()

# Helper to query REST API
def query_sql(sql):
    url = "http://127.0.0.1:8080/api/2.0/sql/queries"
    data = json.dumps({"query": sql}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

# 5. In‑memory SQLite baseline
import sqlite3
def baseline_sqlite():
    start = time.time()
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    rows = [(i, f"value_{i}") for i in range(1000)]
    cur.executemany("INSERT INTO test (id, value) VALUES (?,?)", rows)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM test WHERE id >= 500")
    count = cur.fetchone()[0]
    conn.close()
    duration = time.time() - start
    add_benchmark("sqlite_query_latency_ms", round(duration*1000, 2))
    return count

baseline_count = baseline_sqlite()

# 6. Test minilake SQL insert & query
def test_minilake_sql():
    start = time.time()
    try:
        # create table
        query_sql("CREATE TABLE test (id INT, value STRING)")
        # insert rows
        insert_vals = ", ".join([f"({i}, 'value_{i}')" for i in range(1000)])
        query_sql(f"INSERT INTO test VALUES {insert_vals}")
        # query
        result = query_sql("SELECT COUNT(*) as cnt FROM test WHERE id >= 500")
        cnt = result.get('result', [{}])[0].get('cnt')
        if cnt != 500:
            raise AssertionError(f"Expected 500 rows, got {cnt}")
        print_marker("TEST_PASS:minilake_sql")
    except Exception as e:
        print_marker(f"TEST_FAIL:minilake_sql:{e}")
    finally:
        add_benchmark("minilake_sql_latency_ms", round((time.time() - start)*1000, 2))

test_minilake_sql()

# 7. Benchmark vs baseline
def compare_vs_sqlite():
    try:
        # Use previously collected benchmarks
        ml = next(v for k,v in benchmarks if k=="minilake_sql_latency_ms")
        sl = next(v for k,v in benchmarks if k=="sqlite_query_latency_ms")
        ratio = round(ml / sl, 2) if sl != 0 else float('inf')
        print_marker(f"BENCHMARK:vs_sqlite_sql_latency_ratio:{ratio}")
    except Exception as e:
        print_marker(f"BENCHMARK:vs_sqlite_sql_latency_ratio:fail:{e}")

compare_vs_sqlite()

# 8. Clean up server
def stop_server():
    global server_process
    if server_process:
        server_process.terminate()
        server_process.wait(timeout=5)

stop_server()

# Emit all collected benchmarks (already printed)
print_marker("RUN_OK")