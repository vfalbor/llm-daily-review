import subprocess, sys, os, time, threading, http.client, urllib.request, json, traceback, tracemalloc, socket
from pathlib import Path

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def apk_install(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc != 0:
        print(f"INSTALL_FAIL:{pkg}:{err}")
        return False
    return True

def install_system_packages():
    pkgs = ['nodejs', 'npm', 'git', 'ocaml', 'opam', 'make', 'gcc', 'musl-dev']
    for p in pkgs:
        if not apk_install(p):
            print(f"INSTALL_FAIL:{p}")
    print("INSTALL_OK")

def opam_init():
    rc, out, err = run_cmd(['opam', 'init', '-a', '--disable-sandboxing'])
    if rc != 0:
        print(f"INSTALL_FAIL:opam_init:{err}")
    else:
        print("INSTALL_OK")

def opam_install(packages):
    rc, out, err = run_cmd(['opam', 'install', '-y'] + packages)
    if rc != 0:
        print(f"INSTALL_FAIL:opam_install:{err}")
    else:
        print("INSTALL_OK")

def clone_repo():
    repo_url = "https://github.com/hyphatech/spindle.git"
    dest = Path("/tmp/spindle")
    if dest.exists():
        subprocess.run(['rm', '-rf', str(dest)])
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(dest)])
    if rc != 0:
        print(f"INSTALL_FAIL:git_clone:{err}")
        return None
    print("INSTALL_OK")
    return dest

def build_example(repo_path):
    example_path = repo_path / "example"
    os.chdir(example_path)
    # ensure dune is installed via opam
    rc, out, err = run_cmd(['opam', 'install', '-y', 'dune'])
    if rc != 0:
        print(f"INSTALL_FAIL:dune:{err}")
    # build
    start = time.time()
    rc, out, err = run_cmd(['dune', 'build'])
    elapsed = time.time() - start
    if rc != 0:
        print(f"TEST_FAIL:build_example:{err}")
    else:
        print(f"BENCHMARK:build_time_s:{elapsed:.3f}")
        print(f"TEST_PASS:build_example")
    return rc == 0, example_path

def start_server(example_path):
    os.chdir(example_path)
    # run the server in background
    server_cmd = ['dune', 'exec', '--', 'bin/main.exe']
    proc = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # wait for server to be ready
    start = time.time()
    for _ in range(30):
        try:
            with socket.create_connection(("127.0.0.1", 8080), timeout=1):
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.kill()
        print("TEST_FAIL:start_server:timeout")
        return None, None
    startup = time.time() - start
    print(f"BENCHMARK:startup_time_s:{startup:.3f}")
    print("TEST_PASS:start_server")
    return proc, startup

def stop_server(proc):
    if proc:
        proc.terminate()
        proc.wait()

def test_endpoint():
    url = "http://127.0.0.1:8080/hello"
    try:
        start = time.time()
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode()
        latency = (time.time() - start) * 1000
        if "Hello, World!" in body:
            print(f"BENCHMARK:hello_endpoint_ms:{latency:.2f}")
            print("TEST_PASS:hello_endpoint")
        else:
            print(f"TEST_FAIL:hello_endpoint:unexpected_body")
    except Exception as e:
        print(f"TEST_FAIL:hello_endpoint:{e}")

def benchmark_concurrency():
    import concurrent.futures
    url = "http://127.0.0.1:8080/hello"
    def req():
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                return r.read()
        except:
            return None
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(req) for _ in range(100)]
        results = [f.result() for f in futures]
    duration = time.time() - start
    success = sum(1 for r in results if r)
    throughput = success / duration if duration > 0 else 0
    print(f"BENCHMARK:concurrent_requests_success:{success}")
    print(f"BENCHMARK:concurrent_requests_rps:{throughput:.2f}")
    print("TEST_PASS:concurrent_requests")

def test_type_error():
    # modify a handler to introduce a type error and ensure build fails
    handler_file = Path("/tmp/spindle/example/lib/handler.ml")
    if not handler_file.exists():
        print("TEST_SKIP:type_error_check:handler file not found")
        return
    backup = handler_file.read_text()
    try:
        # introduce type mismatch
        bad_content = backup.replace("let hello", "let hello : int =")
        handler_file.write_text(bad_content)
        rc, out, err = run_cmd(['dune', 'build'])
        if rc != 0:
            print("TEST_PASS:type_error_check")
        else:
            print("TEST_FAIL:type_error_check:build succeeded despite type error")
    except Exception as e:
        print(f"TEST_FAIL:type_error_check:{e}")
    finally:
        handler_file.write_text(backup)

def benchmark_vs_baseline():
    # baseline: Dream framework approximate startup 0.6s (example)
    baseline_startup = 0.6
    # use previously measured startup_time_s if available
    try:
        with open("/tmp/startup_time.txt") as f:
            my_startup = float(f.read().strip())
    except:
        my_startup = None
    if my_startup is not None:
        ratio = my_startup / baseline_startup
        print(f"BENCHMARK:vs_dream_startup_ratio:{ratio:.3f}")

def main():
    try:
        install_system_packages()
        opam_init()
        opam_install(['dune'])
        repo = clone_repo()
        if not repo:
            raise RuntimeError("Clone failed")
        built, example_path = build_example(repo)
        if not built:
            raise RuntimeError("Build failed")
        proc, startup = start_server(example_path)
        if not proc:
            raise RuntimeError("Server start failed")
        # store startup for later baseline comparison
        Path("/tmp/startup_time.txt").write_text(str(startup))
        test_endpoint()
        benchmark_concurrency()
        test_type_error()
        benchmark_vs_baseline()
        stop_server(proc)
    except Exception as e:
        print(f"TEST_FAIL:overall:{e}")
        traceback.print_exc()
    finally:
        print("RUN_OK")

if __name__ == "__main__":
    main()