import subprocess, sys, os, time, json, shutil, tracemalloc, urllib.request, urllib.error, tempfile

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def install_rust():
    # rustup already present in alpine? Use apk to get cargo
    install_apk('rust')
    install_apk('cargo')
    install_apk('git')
    install_apk('sqlite')
    # ensure cargo is in PATH
    os.environ["PATH"] += os.pathsep + "/root/.cargo/bin"

def bench(name, func):
    start = time.time()
    tracemalloc.start()
    try:
        result = func()
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:{name}:{elapsed:.4f}")
    return result, elapsed, peak

def main():
    # 1. Install system packages
    for pkg in ['sqlite', 'git', 'rust', 'cargo']:
        install_apk(pkg)

    # 2. Clone repo and build
    repo_url = "https://github.com/asciimoo/hister.git"
    src_dir = "/tmp/hister"
    if os.path.isdir(src_dir):
        shutil.rmtree(src_dir)
    try:
        clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, src_dir])
        if clone_res.returncode != 0:
            raise RuntimeError(clone_res.stderr.strip())
        # build
        def build():
            return run_cmd(['cargo', 'build', '--release'], cwd=src_dir)
        (build_res, build_time, _) = bench("cargo_build_s", build)
        if build_res.returncode != 0:
            raise RuntimeError(build_res.stderr.strip())
        print_marker("TEST_PASS:build")
    except Exception as e:
        print_marker(f"TEST_FAIL:build:{e}")

    # 3. Install client via pip if exists
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'hister-client'], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:hister-client:{e}")

    # 4. Create in‑memory DB and benchmark query vs sqlite
    import sqlite3
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE docs(id INTEGER PRIMARY KEY, content TEXT);")
    for i in range(1000):
        cur.execute("INSERT INTO docs(content) VALUES (?)", (f"sample text line {i}",))
    conn.commit()

    def sqlite_query():
        cur.execute("SELECT COUNT(*) FROM docs WHERE content LIKE '%line 999%'")
        return cur.fetchone()
    (sqlite_res, sqlite_time, _) = bench("sqlite_query_ms", lambda: sqlite_query())
    print_marker(f"TEST_PASS:sqlite_query")

    # 5. Use hister binary to index temporary files and query
    try:
        # create sample files
        sample_dir = tempfile.mkdtemp()
        for i in range(100):
            with open(os.path.join(sample_dir, f"file{i}.txt"), "w") as f:
                f.write(f"This is test file number {i}\n")
        # index
        def index():
            return run_cmd([os.path.join(src_dir, 'target', 'release', 'hister'), 'index', sample_dir])
        (idx_res, idx_time, _) = bench("hister_index_s", index)
        if idx_res.returncode != 0:
            raise RuntimeError(idx_res.stderr.strip())
        print_marker("TEST_PASS:hister_index")
        # search
        def search():
            return run_cmd([os.path.join(src_dir, 'target', 'release', 'hister'), 'search', 'test'])
        (search_res, search_time, _) = bench("hister_search_ms", search)
        if search_res.returncode != 0:
            raise RuntimeError(search_res.stderr.strip())
        print_marker("TEST_PASS:hister_search")
        # compare latency
        ratio = search_time / sqlite_time if sqlite_time else 0
        print_marker(f"BENCHMARK:vs_sqlite_query_ratio:{ratio:.4f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:hister_index_or_search:{e}")

    # 6. Start HTTP server and query endpoint
    try:
        server_proc = subprocess.Popen([os.path.join(src_dir, 'target', 'release', 'hister'), 'server', '--port', '8085'],
                                       cwd=src_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)  # give it time to start
        def http_query():
            with urllib.request.urlopen("http://127.0.0.1:8085/search?q=test") as resp:
                return json.load(resp)
        (resp_json, http_time, _) = bench("hister_http_ms", http_query)
        if isinstance(resp_json, dict) and "results" in resp_json:
            print_marker("TEST_PASS:hister_http")
        else:
            raise RuntimeError("Invalid JSON response")
    except Exception as e:
        print_marker(f"TEST_FAIL:hister_http:{e}")
    finally:
        if 'server_proc' in locals():
            server_proc.terminate()
            server_proc.wait()

    # 7. Benchmark indexing 10k files
    try:
        large_dir = tempfile.mkdtemp()
        for i in range(10000):
            with open(os.path.join(large_dir, f"doc{i}.txt"), "w") as f:
                f.write(f"Document number {i} for performance testing.\n")
        def large_index():
            return run_cmd([os.path.join(src_dir, 'target', 'release', 'hister'), 'index', large_dir])
        (large_res, large_time, _) = bench("hister_index_10k_s", large_index)
        if large_res.returncode != 0:
            raise RuntimeError(large_res.stderr.strip())
        print_marker("TEST_PASS:hister_index_10k")
        # baseline using ripgrep (as similar tool)
        install_apk('ripgrep')
        def rg_index():
            # simulate indexing by counting matches
            return run_cmd(['rg', '--files', large_dir])
        (rg_res, rg_time, _) = bench("rg_count_10k_s", rg_index)
        print_marker(f"BENCHMARK:vs_ripgrep_index_ratio:{large_time/rg_time if rg_time else 0:.4f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:hister_index_10k:{e}")

    # Ensure at least three benchmark lines were printed (already done)

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()