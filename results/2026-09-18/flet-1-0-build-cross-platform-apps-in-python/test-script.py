#!/usr/bin/env python3
import subprocess, sys, time, os, signal, threading, urllib.request, json, tracemalloc, shutil, pathlib, socket
from contextlib import closing

def apk_install(pkg):
    try:
        subprocess.run(['apk','add','--no-cache',pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def pip_install(pkg):
    try:
        subprocess.run([sys.executable,'-m','pip','install','--quiet',pkg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("INSTALL_OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        return False

def git_clone(repo, dest):
    try:
        subprocess.run(['git','clone','--depth','1',repo,dest], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:git clone {e}")
        return False

def start_server(cmd, cwd):
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc

def wait_port(port, host='127.0.0.1', timeout=10.0):
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((host, port))
                return True
            except OSError:
                time.sleep(0.1)
    return False

def http_get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.read().decode()
    except Exception as e:
        return None

def benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def test_pip_install():
    name = "pip_install_flet"
    try:
        ok = pip_install('flet')
        if ok:
            print(f"TEST_PASS:{name}")
        else:
            print(f"TEST_FAIL:{name}:pip install failed")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_fallback_install():
    name = "fallback_git_install"
    dest = "/tmp/flet_src"
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    if not git_clone('https://github.com/flet-dev/flet.git', dest):
        print(f"TEST_FAIL:{name}:git clone failed")
        return
    try:
        subprocess.run([sys.executable,'-m','pip','install','-e','.', '--quiet'], cwd=dest, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"TEST_PASS:{name}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:{name}:{e}")

def write_minimal_flet_app(path):
    code = """
import flet as ft
def main(page: ft.Page):
    page.title = "Hello"
    page.add(ft.Text("Hello, world!"))
ft.app(target=main, view=ft.WEB_BROWSER, port=8550, server_port=8550, hide=False)
"""
    with open(path,'w') as f:
        f.write(code)

def write_minimal_flask_app(path):
    code = """
from flask import Flask
app = Flask(__name__)
@app.route("/")
def hello():
    return "Hello, world!"
if __name__ == "__main__":
    app.run(port=8560)
"""
    with open(path,'w') as f:
        f.write(code)

def measure_startup(cmd, cwd, port):
    tracemalloc.start()
    start = time.time()
    proc = start_server(cmd, cwd)
    if not wait_port(port, timeout=15):
        proc.kill()
        tracemalloc.stop()
        return None, None, proc
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return end - start, peak / 1024, proc

def test_startup_and_compare():
    name = "startup_vs_flask"
    app_dir = "/tmp/flet_app"
    os.makedirs(app_dir, exist_ok=True)
    flet_path = os.path.join(app_dir, "app.py")
    write_minimal_flet_app(flet_path)

    flask_dir = "/tmp/flask_app"
    os.makedirs(flask_dir, exist_ok=True)
    flask_path = os.path.join(flask_dir, "app.py")
    write_minimal_flask_app(flask_path)

    # install baseline Flask
    pip_install('flask')

    flet_time, flet_mem, flet_proc = measure_startup([sys.executable, flet_path], app_dir, 8550)
    if flet_time is None:
        print(f"TEST_FAIL:{name}:flet did not start")
        return
    flask_time, flask_mem, flask_proc = measure_startup([sys.executable, flask_path], flask_dir, 8560)
    if flask_time is None:
        flet_proc.kill()
        print(f"TEST_FAIL:{name}:flask did not start")
        return

    benchmark("flet_startup_s", round(flet_time,3))
    benchmark("flask_startup_s", round(flask_time,3))
    ratio = flet_time / flask_time if flask_time>0 else 0
    benchmark(f"vs_flask_startup_ratio", round(ratio,3))

    # simple HTTP check
    resp = http_get("http://127.0.0.1:8550/")
    if resp and "Hello, world!" in resp:
        print(f"TEST_PASS:{name}")
    else:
        print(f"TEST_FAIL:{name}:invalid response")

    # cleanup
    flet_proc.kill()
    flask_proc.kill()

def test_http_latency():
    name = "http_latency"
    try:
        start = time.time()
        resp = http_get("http://127.0.0.1:8550/")
        latency = (time.time() - start)*1000
        if resp:
            benchmark("query_latency_ms", round(latency,2))
            print(f"TEST_PASS:{name}")
        else:
            print(f"TEST_FAIL:{name}:no response")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def test_headless_screenshot():
    name = "headless_screenshot"
    try:
        # use playwright if available, otherwise skip
        try:
            import playwright.sync_api as pw
        except ImportError:
            pip_install('playwright')
            import playwright.sync_api as pw
            pw.sync_api._install()
        with pw.sync_playwright().start() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://127.0.0.1:8550", wait_until="networkidle")
            path = "/tmp/flet_screenshot.png"
            page.screenshot(path=path)
            size = os.path.getsize(path)
            benchmark("screenshot_size_bytes", size)
            print(f"TEST_PASS:{name}")
            browser.close()
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def main():
    # Install system deps
    apk_install('nodejs')
    apk_install('npm')
    # Install flet (pip or fallback)
    test_pip_install()
    # If pip failed, try fallback
    try:
        import flet  # noqa: F401
    except Exception:
        test_fallback_install()
    # Run tests
    test_startup_and_compare()
    test_http_latency()
    test_headless_screenshot()
    # Ensure at least 3 benchmark lines (already emitted)
    # Final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()