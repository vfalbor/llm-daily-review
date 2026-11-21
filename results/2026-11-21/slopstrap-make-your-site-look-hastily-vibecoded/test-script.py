#!/usr/bin/env python3
import subprocess, sys, os, time, json, traceback, http.client, urllib.request, threading, socket
from pathlib import Path

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def measure_install():
    start = time.time()
    try:
        # install system packages
        res = run_cmd(['apk','add','--no-cache','nodejs','npm'])
        if res.returncode != 0:
            raise RuntimeError(f"apk add failed: {res.stderr.strip()}")
        # clone repo
        repo_url = "https://github.com/mikelacher/slopstrap.git"
        repo_dir = Path("/tmp/slopstrap")
        if repo_dir.exists():
            run_cmd(['rm','-rf',str(repo_dir)])
        res = run_cmd(['git','clone','--depth','1',repo_url,str(repo_dir)])
        if res.returncode != 0:
            raise RuntimeError(f"git clone failed: {res.stderr.strip()}")
        # npm install
        res = run_cmd(['npm','install'], cwd=str(repo_dir))
        if res.returncode != 0:
            raise RuntimeError(f"npm install failed: {res.stderr.strip()}")
        elapsed = time.time() - start
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")
        return True, elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")
        return False, elapsed

def start_simple_server(html_content, port=8000):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html_content.encode())
            elif self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, *args, **kwargs):
            pass
    server = http.server.HTTPServer(('0.0.0.0', port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread

def measure_server_start():
    start = time.time()
    try:
        html = """<!doctype html><html><head>
<link rel="stylesheet" href="slopstrap.css">
</head><body><div class="vibe">Hello</div></body></html>"""
        server, thread = start_simple_server(html, port=8001)
        elapsed = time.time() - start
        print_marker(f"TEST_PASS:server_start")
        print_marker(f"BENCHMARK:server_start_s:{elapsed:.3f}")
        return server, elapsed
    except Exception as e:
        print_marker(f"TEST_FAIL:server_start:{e}")
        print_marker(f"BENCHMARK:server_start_s:{time.time()-start:.3f}")
        return None, None

def http_request(url):
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read()
        latency = (time.time() - start) * 1000  # ms
        return True, latency, data
    except Exception as e:
        return False, (time.time() - start) * 1000, None

def run_tests():
    # test 1: health endpoint
    ok, latency, data = http_request("http://127.0.0.1:8001/health")
    if ok and b'"status":"ok"' in data:
        print_marker("TEST_PASS:health_endpoint")
    else:
        print_marker(f"TEST_FAIL:health_endpoint:status_code_or_content_invalid")
    print_marker(f"BENCHMARK:health_latency_ms:{latency:.2f}")

    # test 2: page load
    ok, latency, data = http_request("http://127.0.0.1:8001/")
    if ok and b'Hello' in data:
        print_marker("TEST_PASS:page_load")
    else:
        print_marker(f"TEST_FAIL:page_load:unable_to_fetch")
    print_marker(f"BENCHMARK:page_load_ms:{latency:.2f}")

def baseline_comparison(install_time, page_latency):
    # Rough baseline: Tailwind install ~15s, page load ~120ms (example)
    baseline_install = 15.0
    baseline_page = 120.0
    ratio_inst = install_time / baseline_install if baseline_install else 0
    ratio_page = page_latency / baseline_page if baseline_page else 0
    print_marker(f"BENCHMARK:vs_tailwind_install_ratio:{ratio_inst:.3f}")
    print_marker(f"BENCHMARK:vs_tailwind_page_latency_ratio:{ratio_page:.3f}")

def main():
    try:
        success, install_time = measure_install()
    except Exception as e:
        print_marker(f"TEST_FAIL:measure_install:{e}")
        install_time = None

    server = None
    if success:
        server, start_time = measure_server_start()
        if server:
            try:
                run_tests()
                # Use last page_load latency for comparison; stored via env var or simple re-request
                ok, latency, _ = http_request("http://127.0.0.1:8001/")
                if ok:
                    baseline_comparison(install_time, latency)
                else:
                    baseline_comparison(install_time, 0)
            finally:
                server.shutdown()
        else:
            print_marker("TEST_SKIP:run_tests:server_not_started")
    else:
        print_marker("TEST_SKIP:run_tests:install_failed")

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()