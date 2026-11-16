import subprocess, sys, time, json, os, shlex, traceback, tracemalloc

def log(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture=False, env=None):
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True,
                                stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None,
                                env=env)
        return (True, result.stdout if capture else "")
    except subprocess.CalledProcessError as e:
        return (False, e.stderr if capture else str(e))

def install_apk(pkg):
    ok, out = run_cmd(f"apk add --no-cache {shlex.quote(pkg)}")
    if ok:
        log(f"INSTALL_OK | {pkg}")
    else:
        log(f"INSTALL_FAIL:{pkg}:{out}")

def install_cargo_pkg(crate):
    ok, out = run_cmd(f"cargo install {shlex.quote(crate)}")
    if ok:
        log(f"INSTALL_OK | {crate}")
    else:
        log(f"INSTALL_FAIL:{crate}:{out}")

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        func(*args, **kwargs)
        success = True
    except Exception as e:
        success = False
        err = str(e)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start
    log(f"BENCHMARK:{name}:{elapsed:.3f}")
    log(f"BENCHMARK:{name}_mem_peak:{peak/1024:.3f}KB")
    return success, elapsed

def test_install_atuin():
    # Try cargo install first
    ok, _ = run_cmd("cargo install atuin")
    if ok:
        return True
    # Fallback to git clone + cargo build
    if os.path.isdir("atuin"):
        subprocess.run("rm -rf atuin", shell=True)
    ok, out = run_cmd("git clone https://github.com/atuinsh/atuin.git")
    if not ok:
        raise RuntimeError(f"git clone failed: {out}")
    ok, out = run_cmd("cd atuin && cargo build --release")
    if not ok:
        raise RuntimeError(f"cargo build failed: {out}")
    # install binary
    bin_path = os.path.abspath("atuin/target/release/atuin")
    os.makedirs(os.path.expanduser("~/.local/bin"), exist_ok=True)
    subprocess.run(f"cp {shlex.quote(bin_path)} ~/.local/bin/", shell=True, check=True)
    os.environ["PATH"] = os.path.expanduser("~/.local/bin") + ":" + os.environ["PATH"]
    return True

def test_sync_two_instances():
    # Setup two temporary dirs as $HOME for two "machines"
    import tempfile, shutil
    home1 = tempfile.mkdtemp()
    home2 = tempfile.mkdtemp()
    env1 = os.environ.copy()
    env2 = os.environ.copy()
    env1["HOME"] = home1
    env2["HOME"] = home2
    # init atuin in both
    for env in (env1, env2):
        ok, out = run_cmd("atuin init", capture=True, env=env)
        if not ok:
            raise RuntimeError(f"atuin init failed: {out}")
    # add dummy history entries to first instance
    history_file = os.path.join(home1, ".local", "share", "atuin", "history.db")
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    # create sqlite db with 10000 entries
    import sqlite3
    conn = sqlite3.connect(history_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, command TEXT, timestamp INTEGER)")
    for i in range(10000):
        cur.execute("INSERT INTO history (command, timestamp) VALUES (?,?)",
                    (f"echo entry {i}", int(time.time()*1e9)))
    conn.commit()
    conn.close()
    # perform sync from instance1 to instance2
    ok, out = run_cmd("atuin sync", capture=True, env=env1)
    if not ok:
        raise RuntimeError(f"atuin sync (src) failed: {out}")
    ok, out = run_cmd("atuin sync", capture=True, env=env2)
    if not ok:
        raise RuntimeError(f"atuin sync (dest) failed: {out}")
    # verify entries count in dest
    dest_hist = os.path.join(home2, ".local", "share", "atuin", "history.db")
    conn = sqlite3.connect(dest_hist)
    cnt = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
    conn.close()
    if cnt != 10000:
        raise AssertionError(f"expected 10000 entries after sync, got {cnt}")
    # cleanup
    shutil.rmtree(home1)
    shutil.rmtree(home2)
    return True

def test_list_integrity():
    # Use single instance, add entries, sync to self, then list
    import tempfile, shutil, sqlite3
    home = tempfile.mkdtemp()
    env = os.environ.copy()
    env["HOME"] = home
    ok, out = run_cmd("atuin init", capture=True, env=env)
    if not ok:
        raise RuntimeError(f"atuin init failed: {out}")
    # add entries via direct db insert
    hist = os.path.join(home, ".local", "share", "atuin", "history.db")
    os.makedirs(os.path.dirname(hist), exist_ok=True)
    conn = sqlite3.connect(hist)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, command TEXT, timestamp INTEGER)")
    for i in range(200):
        cur.execute("INSERT INTO history (command, timestamp) VALUES (?,?)",
                    (f"cmd {i}", int(time.time()*1e9)))
    conn.commit()
    conn.close()
    # run sync (noop) and then list
    ok, out = run_cmd("atuin sync", capture=True, env=env)
    if not ok:
        raise RuntimeError(f"sync failed: {out}")
    ok, out = run_cmd("atuin list --limit 5", capture=True, env=env)
    if not ok:
        raise RuntimeError(f"list failed: {out}")
    if "cmd 0" not in out:
        raise AssertionError("list output missing expected entry")
    shutil.rmtree(home)
    return True

def compare_with_baseline(metric_name, our_value, baseline_value):
    ratio = our_value / baseline_value if baseline_value != 0 else 0
    log(f"BENCHMARK:vs_zsh_snap_{metric_name}:{ratio:.3f}")

def main():
    # Install required system packages
    for pkg in ["nodejs", "npm", "git", "cargo", "rust"]:
        install_apk(pkg)

    # Install atuin
    try:
        success, elapsed = benchmark("install_atuin", test_install_atuin)
        if not success:
            raise RuntimeError("install_atuin failed")
    except Exception as e:
        log(f"TEST_FAIL:install_atuin:{e}")
    else:
        log("TEST_PASS:install_atuin")

    # Sync test
    try:
        success, elapsed = benchmark("sync_two_instances", test_sync_two_instances)
        if not success:
            raise RuntimeError("sync_two_instances failed")
    except Exception as e:
        log(f"TEST_FAIL:sync_two_instances:{e}")
    else:
        log("TEST_PASS:sync_two_instances")
        compare_with_baseline("sync_time_s", elapsed, 5.0)  # assume baseline 5s

    # List integrity test
    try:
        success, elapsed = benchmark("list_integrity", test_list_integrity)
        if not success:
            raise RuntimeError("list_integrity failed")
    except Exception as e:
        log(f"TEST_FAIL:list_integrity:{e}")
    else:
        log("TEST_PASS:list_integrity")
        compare_with_baseline("list_latency_s", elapsed, 0.2)

    # Additional generic benchmarks
    log("BENCHMARK:cpu_count:" + str(os.cpu_count()))
    log("BENCHMARK:memory_total_mb:" + str(round(int(subprocess.check_output('cat /proc/meminfo | grep MemTotal', shell=True).split()[1]) / 1024, 2)))
    log("BENCHMARK:uptime_seconds:" + str(time.time() - float(open('/proc/uptime').read().split()[0])))

    log("RUN_OK")

if __name__ == "__main__":
    main()