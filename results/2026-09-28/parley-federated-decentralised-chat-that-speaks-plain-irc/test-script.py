import subprocess, sys, time, tracemalloc, os, shutil, json, socket, threading

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err.strip()}")
    return rc == 0

def pip_install(package):
    start = time.time()
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
    elapsed = time.time() - start
    print(f"BENCHMARK:install_time_s:{elapsed:.3f}")
    if rc == 0:
        print("INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:{package}:{err.strip()}")
        return False

def git_clone(repo, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    if rc == 0:
        print("INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:git_clone:{err.strip()}")
        return False

def pip_install_editable(path):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    if rc == 0:
        print("INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:editable_install:{err.strip()}")
        return False

def benchmark_import():
    start = time.time()
    tracemalloc.start()
    try:
        import parley
        import_time = (time.time() - start) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print(f"BENCHMARK:import_mem_kb:{peak/1024:.2f}")
        print("TEST_PASS:import_parley")
    except Exception as e:
        print(f"TEST_FAIL:import_parley:{e}")

def start_server(dir_path):
    # Assume server can be started via `python -m parley.server`
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen([sys.executable, '-m', 'parley.server'], cwd=dir_path,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return proc

def wait_for_port(host, port, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except Exception:
                time.sleep(0.1)
    return False

def test_message_delivery():
    try:
        # Simple in-process simulation using the library if available
        from parley.client import Client
        from parley.server import Server

        host = "127.0.0.1"
        port = 6667

        server = Server(host=host, port=port)
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()
        if not wait_for_port(host, port):
            raise RuntimeError("Server did not start")

        client_a = Client(host, port, nick="alice")
        client_b = Client(host, port, nick="bob")
        client_a.connect()
        client_b.connect()
        time.sleep(0.2)  # allow registration

        start = time.time()
        client_a.send_message("#test", "hello from alice")
        # naive poll for message on client_b
        deadline = time.time() + 5
        received = False
        while time.time() < deadline:
            msgs = client_b.fetch_messages()
            if any("hello from alice" in m for m in msgs):
                received = True
                break
            time.sleep(0.1)
        latency = (time.time() - start) * 1000

        server.stop()
        server_thread.join()

        if received:
            print(f"BENCHMARK:msg_latency_ms:{latency:.2f}")
            print("TEST_PASS:message_delivery")
        else:
            print("TEST_FAIL:message_delivery:Message not received")
    except Exception as e:
        print(f"TEST_FAIL:message_delivery:{e}")

def compare_baseline():
    # Assume baseline Matrix client latency ~120ms for similar test
    baseline = 120.0
    try:
        with open("benchmark.json", "r") as f:
            data = json.load(f)
        latency = data.get("msg_latency_ms")
        if latency:
            ratio = latency / baseline
            print(f"BENCHMARK:vs_matrix_latency_ratio:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install apk packages
    install_apk('git')

    # 2. Try pip install
    if not pip_install('parley'):
        # fallback to git clone + editable install
        repo = "https://git.mills.io/prologic/parley.git"
        src_dir = "/tmp/parley_src"
        if git_clone(repo, src_dir):
            pip_install_editable(src_dir)

    # 3. Benchmark import
    benchmark_import()

    # 4. Test message delivery (includes building server)
    test_message_delivery()

    # 5. Emit additional benchmarks (loc count, file count)
    try:
        repo_path = "/tmp/parley_src"
        if os.path.isdir(repo_path):
            file_count = sum(len(files) for _, _, files in os.walk(repo_path))
            print(f"BENCHMARK:test_files_count:{file_count}")
            # simplistic lines of code count
            loc = 0
            for root, _, files in os.walk(repo_path):
                for f in files:
                    if f.endswith('.py'):
                        with open(os.path.join(root, f), 'r', errors='ignore') as fh:
                            loc += sum(1 for _ in fh)
            print(f"BENCHMARK:loc_count:{loc}")
    except Exception as e:
        print(f"TEST_FAIL:benchmark_counts:{e}")

    # 6. Compare vs baseline
    compare_baseline()

    # Final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()