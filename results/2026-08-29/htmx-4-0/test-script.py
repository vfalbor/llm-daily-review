import subprocess, sys, time, os, json, threading, http.server, socketserver, urllib.request, traceback, tracemalloc, random, string, pathlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk_packages():
    pkgs = ["nodejs", "npm"]
    try:
        start = time.time()
        result = run_cmd(['apk', 'add', '--no-cache'] + pkgs, check=False)
        elapsed = time.time() - start
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        print_marker(f"INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        elapsed = 0.0
    print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")

def npm_install_htmx():
    try:
        start = time.time()
        result = run_cmd(['npm', 'install', 'htmx.org'], check=False)
        elapsed = time.time() - start
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        print_marker("TEST_PASS:npm_install_htmx")
    except Exception as e:
        print_marker(f"TEST_FAIL:npm_install_htmx:{e}")
        elapsed = 0.0
    print_marker(f"BENCHMARK:npm_install_time_s:{elapsed:.3f}")

def start_simple_server(root_dir, port):
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(root_dir)
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread

def create_test_page(dir_path):
    html_content = """<!DOCTYPE html>
<html>
<head>
<script src="node_modules/htmx.org/dist/htmx.min.js"></script>
</head>
<body>
<button id="loadBtn" hx-get="/data.json" hx-target="#result">Load Data</button>
<div id="result"></div>
</body>
</html>"""
    data_content = json.dumps({"message": "hello world"})
    (dir_path / "index.html").write_text(html_content)
    (dir_path / "data.json").write_text(data_content)

def measure_hx_get(port):
    try:
        start = time.time()
        resp = urllib.request.urlopen(f'http://127.0.0.1:{port}/data.json')
        _ = resp.read()
        latency = (time.time() - start) * 1000  # ms
        print_marker(f"TEST_PASS:hx_get_request")
        print_marker(f"BENCHMARK:hx_get_latency_ms:{latency:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:hx_get_request:{e}")

def performance_test(port, count=100):
    try:
        start = time.time()
        urls = [f'http://127.0.0.1:{port}/data.json' for _ in range(count)]
        def fetch(url):
            try:
                urllib.request.urlopen(url).read()
            except:
                pass
        threads = [threading.Thread(target=fetch, args=(u,)) for u in urls]
        for t in threads: t.start()
        for t in threads: t.join()
        total = time.time() - start
        avg_ms = (total / count) * 1000
        print_marker(f"BENCHMARK:hx_concurrent_avg_ms:{avg_ms:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:performance_test:{e}")

def compare_vs_baseline(metric, value, baseline):
    try:
        ratio = value / baseline if baseline != 0 else 0
        print_marker(f"BENCHMARK:vs_alpine_{metric}_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_vs_baseline:{e}")

def main():
    tracemalloc.start()
    install_apk_packages()
    npm_install_htmx()

    # setup test files
    workdir = pathlib.Path("/tmp/htmx_test")
    workdir.mkdir(parents=True, exist_ok=True)
    create_test_page(workdir)

    # start server
    try:
        server_port = 8000
        httpd, thr = start_simple_server(workdir, server_port)
        time.sleep(0.5)  # give server time
        print_marker("TEST_PASS:server_start")
    except Exception as e:
        print_marker(f"TEST_FAIL:server_start:{e}")
        httpd = None

    # measure hx-get (simulated via direct request)
    if httpd:
        measure_hx_get(server_port)
        performance_test(server_port, count=100)

    # benchmark memory usage
    current, peak = tracemalloc.get_traced_memory()
    print_marker(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

    # compare one metric vs a baseline (e.g., baseline avg 120ms)
    compare_vs_baseline("hx_concurrent_avg_ms", float(current/1024), 120.0)

    # cleanup
    if httpd:
        httpd.shutdown()

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()