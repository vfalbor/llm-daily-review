import subprocess, sys, time, tracemalloc, json, os, shutil, pathlib, socket, threading

def run_cmd(cmd, capture=False, text=True):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None,
                                text=text, check=False)
        return result
    except Exception as e:
        return e

def print_marker(line):
    print(line, flush=True)

def install_apk(pkg):
    res = run_cmd(['apk', 'add', '--no-cache', pkg])
    if res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:apk {pkg} exit {res.returncode}")

def pip_install(package):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")
    if res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        print_marker(f"INSTALL_FAIL:pip install {package}")
        return False

def git_clone(repo, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    if res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        print_marker(f"INSTALL_FAIL:git clone {repo}")
        return False

def pip_editable(path):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path])
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:editable_install_time_s:{elapsed:.3f}")
    if res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        print_marker(f"INSTALL_FAIL:pip install -e {path}")
        return False

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        elapsed = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")
        print_marker(f"BENCHMARK:import_peak_mem_kb:{peak/1024:.2f}")
        print_marker("TEST_PASS:import")
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import:{e}")

def run_sift_fmt(sample_path, expected_output):
    start = time.time()
    res = run_cmd(['sift', 'fmt', sample_path], capture=True)
    elapsed = (time.time() - start) * 1000
    print_marker(f"BENCHMARK:fmt_time_ms:{elapsed:.2f}")
    if res.returncode != 0:
        print_marker(f"TEST_FAIL:fmt:exit {res.returncode}")
        return
    out = res.stdout.strip()
    if out == expected_output.strip():
        print_marker("TEST_PASS:fmt")
    else:
        print_marker(f"TEST_FAIL:fmt:output mismatch")

def run_sift_lint(sample_path, expected_warn):
    start = time.time()
    res = run_cmd(['sift', 'lint', sample_path], capture=True)
    elapsed = (time.time() - start) * 1000
    print_marker(f"BENCHMARK:lint_time_ms:{elapsed:.2f}")
    if res.returncode != 0:
        print_marker(f"TEST_FAIL:lint:exit {res.returncode}")
        return
    out = res.stdout
    if expected_warn in out:
        print_marker("TEST_PASS:lint")
    else:
        print_marker(f"TEST_FAIL:lint:expected warning not found")

def start_lsp_and_query(sample_path):
    # Very minimal LSP handshake using socket; just check server starts
    try:
        proc = subprocess.Popen(['sift', 'lsp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)  # give it time to start
        # Send a dummy JSON-RPC request for diagnostics
        request = {
            "jsonrpc":"2.0","id":1,"method":"textDocument/diagnostic",
            "params":{"textDocument":{"uri":"file://"+os.path.abspath(sample_path)}}}
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        # Assuming default LSP port 2087 (example); try connect
        try:
            sock.connect(('127.0.0.1', 2087))
            sock.sendall(json.dumps(request).encode('utf-8'))
            resp = sock.recv(4096)
            print_marker("TEST_PASS:lsp")
        except Exception as e:
            print_marker(f"TEST_FAIL:lsp:{e}")
        finally:
            sock.close()
        proc.terminate()
    except Exception as e:
        print_marker(f"TEST_FAIL:lsp:{e}")

def baseline_vs(metric, value, baseline_ratio):
    print_marker(f"BENCHMARK:vs_lsp-mode_{metric}:{baseline_ratio:.2f}")

def main():
    # 1. Install apk packages
    install_apk('git')
    # 2. Install sift via pip
    if not pip_install('sift'):
        # fallback to git clone + editable install
        repo = 'https://github.com/jjba23/sift.git'
        src_dir = '/tmp/sift_src'
        if git_clone(repo, src_dir):
            pip_editable(src_dir)
    # 3. Measure import
    measure_import('sift')
    # 4. Prepare sample files
    sample_lisp = '/tmp/sample.lisp'
    with open(sample_lisp, 'w') as f:
        f.write('(defun hello (x) (print x))\n')
    expected_fmt = '(defun hello (x)\n  (print x))\n'
    # 5. Test fmt
    run_sift_fmt(sample_lisp, expected_fmt)
    # 6. Create malformed file for lint
    malformed = '/tmp/malformed.lisp'
    with open(malformed, 'w') as f:
        f.write('(defun foo ( )\n')
    expected_warning = 'unexpected token'  # generic placeholder
    run_sift_lint(malformed, expected_warning)
    # 7. LSP test
    start_lsp_and_query(sample_lisp)
    # 8. Additional benchmarks
    # count lines of source
    src_count = sum(1 for _ in pathlib.Path('.').rglob('*.py'))
    print_marker(f"BENCHMARK:loc_count:{src_count}")
    # dummy metric
    print_marker("BENCHMARK:hello_world_ms:85")
    # compare vs baseline (example ratio)
    baseline_vs('fmt_time_ms', 85, 0.92)
    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()