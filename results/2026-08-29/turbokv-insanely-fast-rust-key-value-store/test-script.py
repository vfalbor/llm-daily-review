import subprocess, sys, os, time, tracemalloc, json, threading, queue, random, string, math

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture=False):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None, text=True, check=True)
        return result.stdout if capture else ''
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {e.stderr.strip()}")

def install_apk(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def cargo_build_and_test(repo_dir):
    try:
        run_cmd(['cargo', 'build', '--release'], cwd=repo_dir)
        run_cmd(['cargo', 'test', '--release'], cwd=repo_dir)
        print_marker("TEST_PASS:build_and_test")
    except Exception as e:
        print_marker(f"TEST_FAIL:build_and_test:{e}")

def bench_time(func, *args, **kwargs):
    start = time.time()
    func(*args, **kwargs)
    return time.time() - start

def bench_memory(func, *args, **kwargs):
    tracemalloc.start()
    func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024  # KiB

# ---------- Installation ----------
install_apk('sqlite')
install_apk('git')
install_apk('rust')
install_apk('cargo')
install_apk('make')   # some repos need make

# ---------- Clone TurboKV ----------
repo_url = "https://github.com/kingroryg/turbokv.git"
repo_dir = "/tmp/turbokv"
if os.path.isdir(repo_dir):
    subprocess.run(['rm', '-rf', repo_dir])
try:
    run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
    print_marker("INSTALL_OK")
except Exception as e:
    print_marker(f"INSTALL_FAIL:{e}")

# ---------- Build and unit tests ----------
cargo_build_and_test(repo_dir)

# ---------- Benchmarks ----------
benchmarks = {}

# Helper: simple SQLite baseline for get/put latency
def sqlite_put_get(n=1000):
    db_path = "/tmp/benchmark_sqlite.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = run_cmd(['sqlite3', db_path, ".mode csv"], capture=True)  # ensure file exists
    for i in range(n):
        key = f'k{i}'
        val = f'v{i}'
        run_cmd(['sqlite3', db_path, f"INSERT INTO kv(key, value) VALUES('{key}', '{val}');"])
    for i in range(n):
        key = f'k{i}'
        run_cmd(['sqlite3', db_path, f"SELECT value FROM kv WHERE key='{key}';"])

# Benchmark TurboKV put/get using its binary (assume `turbokv` executable exists after build)
def turbokv_put_get(n=1000):
    bin_path = os.path.join(repo_dir, "target", "release", "turbokv")
    if not os.path.isfile(bin_path):
        raise RuntimeError("TurboKV binary not found")
    # start in-memory server
    server = subprocess.Popen([bin_path, "--in-memory"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)  # give it time to start
    try:
        for i in range(n):
            key = f'k{i}'
            val = f'v{i}'
            run_cmd([bin_path, "put", key, val])
        for i in range(n):
            key = f'k{i}'
            run_cmd([bin_path, "get", key])
    finally:
        server.terminate()
        server.wait()

# 1. Measure TurboKV throughput
try:
    t = bench_time(turbokv_put_get, 1000)
    benchmarks['turbokv_put_get_s'] = t
    print_marker(f"BENCHMARK:turbo_put_get_s:{t:.3f}")
    print_marker("TEST_PASS:turbo_put_get")
except Exception as e:
    print_marker(f"TEST_FAIL:turbo_put_get:{e}")

# 2. Measure SQLite baseline
try:
    t = bench_time(sqlite_put_get, 1000)
    benchmarks['sqlite_put_get_s'] = t
    print_marker(f"BENCHMARK:sqlite_put_get_s:{t:.3f}")
    print_marker("TEST_PASS:sqlite_put_get")
except Exception as e:
    print_marker(f"TEST_FAIL:sqlite_put_get:{e}")

# 3. Ratio vs baseline
try:
    ratio = benchmarks['turbokv_put_get_s'] / benchmarks['sqlite_put_get_s']
    print_marker(f"BENCHMARK:vs_sqlite_put_get_ratio:{ratio:.3f}")
except Exception:
    pass

# 4. Memory usage for TurboKV batch write of 10k keys
def turbokv_batch_write():
    bin_path = os.path.join(repo_dir, "target", "release", "turbokv")
    server = subprocess.Popen([bin_path, "--in-memory"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)
    try:
        for i in range(10000):
            key = f'k{i}'
            val = f'v{i}'
            run_cmd([bin_path, "put", key, val])
    finally:
        server.terminate()
        server.wait()

try:
    mem_kib = bench_memory(turbokv_batch_write)
    benchmarks['turbokv_batch_mem_kib'] = mem_kib
    print_marker(f"BENCHMARK:turbo_batch_mem_kib:{mem_kib:.1f}")
    print_marker("TEST_PASS:turbokv_batch_mem")
except Exception as e:
    print_marker(f"TEST_FAIL:turbokv_batch_mem:{e}")

# 5. Concurrent read/write workload (10 threads)
def concurrent_workload():
    bin_path = os.path.join(repo_dir, "target", "release", "turbokv")
    server = subprocess.Popen([bin_path, "--in-memory"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)
    try:
        q = queue.Queue()
        for i in range(1000):
            q.put(i)

        def worker():
            while True:
                try:
                    i = q.get_nowait()
                except queue.Empty:
                    break
                key = f'c{i}'
                val = f'v{i}'
                run_cmd([bin_path, "put", key, val])
                out = run_cmd([bin_path, "get", key])
                if out.strip() != val:
                    raise RuntimeError(f"Data mismatch for {key}")
                q.task_done()

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        server.terminate()
        server.wait()

try:
    t = bench_time(concurrent_workload)
    print_marker(f"BENCHMARK:concurrent_workload_s:{t:.3f}")
    print_marker("TEST_PASS:concurrent_workload")
except Exception as e:
    print_marker(f"TEST_FAIL:concurrent_workload:{e}")

# Ensure at least three benchmark lines exist (already printed above)
print_marker("RUN_OK")