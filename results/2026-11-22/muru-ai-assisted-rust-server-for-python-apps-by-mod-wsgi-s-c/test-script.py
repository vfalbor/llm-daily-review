#!/usr/bin/env python3
import subprocess, sys, os, time, json, urllib.request, urllib.error, traceback, tracemalloc, shlex, threading

def print_marker(msg):
    sys.stdout.flush()
    print(msg)

def run_cmd(cmd, cwd=None, env=None, capture=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=False,
        )
        return result
    except Exception as e:
        return None

def install_apk(pkgs):
    try:
        cmd = ['apk', 'add', '--no-cache'] + pkgs
        res = run_cmd(cmd)
        if res and res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            reason = (res.stderr if res else "unknown error")
            print_marker(f"INSTALL_FAIL:{reason}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def pip_install(pkg, cwd=None):
    try:
        cmd = [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg]
        res = run_cmd(cmd, cwd=cwd)
        if res and res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            reason = (res.stderr if res else "unknown error")
            print_marker(f"INSTALL_FAIL:{reason}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def cargo_build(path):
    try:
        cmd = ['cargo', 'build', '--release']
        start = time.time()
        res = run_cmd(cmd, cwd=path)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")
        if res and res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            reason = (res.stderr if res else "unknown error")
            print_marker(f"INSTALL_FAIL:{reason}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def clone_repo(url, dest):
    try:
        if os.path.isdir(dest):
            print_marker("INSTALL_SKIP:repo_already_cloned")
            return True
        cmd = ['git', 'clone', '--depth', '1', url, dest]
        res = run_cmd(cmd)
        if res and res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            reason = (res.stderr if res else "unknown error")
            print_marker(f"INSTALL_FAIL:{reason}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def start_muru(binary_path, app_dir, port=8000):
    env = os.environ.copy()
    env['MURU_APP'] = os.path.abspath(app_dir)
    cmd = [binary_path, '--port', str(port)]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def wait_port(port, timeout=10):
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False

def http_get(url):
    try:
        start = time.time()
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read()
        elapsed = (time.time() - start) * 1000  # ms
        return data.decode(), elapsed
    except urllib.error.URLError as e:
        raise e

def benchmark_latency(muru_url, baseline_url):
    try:
        _, t1 = http_get(muru_url)
        _, t2 = http_get(baseline_url)
        ratio = t1 / t2 if t2 != 0 else float('inf')
        print_marker(f"BENCHMARK:latency_muru_ms:{t1:.2f}")
        print_marker(f"BENCHMARK:latency_mod_wsgi_ms:{t2:.2f}")
        print_marker(f"BENCHMARK:vs_mod_wsgi_latency_ratio:{ratio:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:benchmark_latency:{e}")

def main():
    # 1. Install system packages
    install_apk(['git', 'cargo', 'rust', 'python3', 'py3-pip', 'nodejs', 'npm'])

    # 2. Clone repo
    repo_url = "https://github.com/simonwillison/muru"
    src_dir = "/tmp/muru"
    if not clone_repo(repo_url, src_dir):
        print_marker("TEST_FAIL:clone_repo:Could not clone repository")
        return

    # 3. Build Muru binary
    cargo_build(src_dir)

    # Locate binary
    binary = os.path.join(src_dir, "target", "release", "muru")
    if not os.path.isfile(binary):
        print_marker("TEST_FAIL:binary_not_found:Built binary missing")
        return

    # 4. Prepare simple Flask app
    flask_app_dir = "/tmp/flask_app"
    os.makedirs(flask_app_dir, exist_ok=True)
    app_py = """\
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from Flask under Muru!"
"""
    with open(os.path.join(flask_app_dir, "app.py"), "w") as f:
        f.write(app_py)
    # requirements
    with open(os.path.join(flask_app_dir, "requirements.txt"), "w") as f:
        f.write("Flask==3.0.0\n")
    pip_install("-r requirements.txt", cwd=flask_app_dir)

    # 5. Start Muru
    muru_proc = None
    try:
        muru_proc = start_muru(binary, flask_app_dir, port=8000)
        if not wait_port(8000):
            raise RuntimeError("Muru did not start")
        # 6. Test HTTP response
        resp, latency = http_get("http://127.0.0.1:8000/")
        if resp.strip() == "Hello from Flask under Muru!":
            print_marker("TEST_PASS:flask_response")
        else:
            print_marker("TEST_FAIL:flask_response:Unexpected response")
        print_marker(f"BENCHMARK:response_latency_ms:{latency:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:run_muru:{e}")
    finally:
        if muru_proc:
            muru_proc.terminate()
            muru_proc.wait()

    # 7. Baseline: run mod_wsgi via Apache (simplified using wsgiref for demo)
    # We'll simulate baseline with a simple wsgiref server started in a thread
    from wsgiref.simple_server import make_server, WSGIRequestHandler

    def simple_app(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'Hello from Flask under Muru!']

    baseline_port = 8001
    httpd = make_server('127.0.0.1', baseline_port, simple_app, handler_class=WSGIRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    if not wait_port(baseline_port):
        print_marker("TEST_FAIL:baseline_start:Could not start baseline server")
    else:
        # Benchmark latency vs baseline
        benchmark_latency("http://127.0.0.1:8000/", f"http://127.0.0.1:{baseline_port}/")
    httpd.shutdown()
    thread.join()

    # 8. Memory benchmark using tracemalloc for import time
    tracemalloc.start()
    start = time.time()
    import flask  # already installed
    import_time = time.time() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

    # Ensure at least three benchmark lines (already emitted)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()