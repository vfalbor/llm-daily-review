import subprocess, sys, time, json, os, threading, http.server, socketserver, traceback, tracemalloc, urllib.request, urllib.error

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

# Install system packages
def apk_install(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return True, ""
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

# Install npm packages
def npm_install(pkg):
    try:
        res = subprocess.run(['npm', 'install', pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return True, ""
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

# Simple HTTP server for static files
class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_http_server(port, directory):
    os.chdir(directory)
    handler = QuietHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd

def stop_http_server(server):
    server.shutdown()
    server.server_close()

def run():
    # 1. Install required APK packages
    pkgs = ['nodejs', 'npm']
    for p in pkgs:
        ok, reason = apk_install(p)
        if ok:
            marker("INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:{reason}")

    # 2. Install jquery via npm
    start = time.time()
    ok, reason = npm_install('jquery@4.1.0')
    install_time = time.time() - start
    if ok:
        marker("INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:{reason}")

    marker(f"BENCHMARK:install_time_s:{install_time:.3f}")

    # 3. Test requiring jquery in node
    test_name = "require_version"
    try:
        node_script = """
const jquery = require('jquery');
console.log(jquery.fn.jquery);
"""
        script_path = "/tmp/require_jquery.js"
        with open(script_path, "w") as f:
            f.write(node_script)
        start = time.time()
        res = subprocess.run(['node', script_path], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            version = res.stdout.strip()
            if version.startswith("4.1.0"):
                marker(f"TEST_PASS:{test_name}")
            else:
                marker(f"TEST_FAIL:{test_name}:unexpected version {version}")
        else:
            marker(f"TEST_FAIL:{test_name}:{res.stderr.strip()}")
        marker(f"BENCHMARK:{test_name}_ms:{duration*1000:.2f}")
    except Exception as e:
        marker(f"TEST_FAIL:{test_name}:{e}")

    # 4. Create HTML page and verify $ is defined
    test_name = "html_load_$"
    try:
        html_dir = "/tmp/jquery_test"
        os.makedirs(html_dir, exist_ok=True)
        html_path = os.path.join(html_dir, "index.html")
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <script src="node_modules/jquery/dist/jquery.min.js"></script>
  <script>
    document.title = typeof $ === 'function' ? 'ok' : 'fail';
  </script>
</head>
<body></body>
</html>"""
        with open(html_path, "w") as f:
            f.write(html_content)

        server = start_http_server(8000, html_dir)
        start = time.time()
        try:
            resp = urllib.request.urlopen("http://localhost:8000/index.html", timeout=5)
            page = resp.read().decode()
        finally:
            stop_http_server(server)
        duration = time.time() - start

        if "title>ok" in page:
            marker(f"TEST_PASS:{test_name}")
        else:
            marker(f"TEST_FAIL:{test_name}:$ not defined")
        marker(f"BENCHMARK:{test_name}_ms:{duration*1000:.2f}")
    except Exception as e:
        marker(f"TEST_FAIL:{test_name}:{e}")

    # 5. Benchmark DOM query on 5000-element list using jsdom via node
    test_name = "dom_query_5000"
    try:
        node_script = """
const { JSDOM } = require('jsdom');
const jquery = require('jquery');
const html = '<ul>' + Array.from({length:5000},(_,i)=>`<li id="item${i}">Item${i}</li>`).join('') + '</ul>';
const dom = new JSDOM(html);
const $ = jquery(dom.window);
const start = Date.now();
const items = $('li');
const duration = Date.now() - start;
console.log(items.length, duration);
"""
        script_path = "/tmp/dom_query.js"
        with open(script_path, "w") as f:
            f.write(node_script)
        # ensure jsdom installed
        npm_install('jsdom')
        start = time.time()
        res = subprocess.run(['node', script_path], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            count, ms = res.stdout.strip().split()
            marker(f"TEST_PASS:{test_name}")
            marker(f"BENCHMARK:{test_name}_count:{int(count)}")
            marker(f"BENCHMARK:{test_name}_ms:{float(ms):.2f}")
        else:
            marker(f"TEST_FAIL:{test_name}:{res.stderr.strip()}")
    except Exception as e:
        marker(f"TEST_FAIL:{test_name}:{e}")

    # 6. Benchmark Ajax GET using jquery vs fetch
    test_name = "ajax_vs_fetch"
    try:
        # Simple http server that returns json quickly
        class JsonHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"msg":"ok"}')
            def log_message(self, *args):
                pass

        httpd = socketserver.TCPServer(("", 8001), JsonHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        node_script = """
const jquery = require('jquery');
function ajaxPromise() {
  return new Promise((resolve, reject) => {
    jquery.ajax({url: 'http://localhost:8001/', method: 'GET', success: resolve, error: reject});
  });
}
function fetchPromise() {
  return fetch('http://localhost:8001/').then(r=>r.json());
}
(async () => {
  const startJ = Date.now();
  await ajaxPromise();
  const durJ = Date.now() - startJ;
  const startF = Date.now();
  await fetchPromise();
  const durF = Date.now() - startF;
  console.log(durJ, durF);
})();
"""
        script_path = "/tmp/ajax_vs_fetch.js"
        with open(script_path, "w") as f:
            f.write(node_script)
        # ensure fetch is available (node 18+ has global fetch)
        start = time.time()
        res = subprocess.run(['node', script_path], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        total = time.time() - start
        if res.returncode == 0:
            durJ, durF = map(float, res.stdout.strip().split())
            marker(f"TEST_PASS:{test_name}")
            marker(f"BENCHMARK:{test_name}_jquery_ms:{durJ:.2f}")
            marker(f"BENCHMARK:{test_name}_fetch_ms:{durF:.2f}")
            # compare ratio jquery/fetch
            ratio = durJ / durF if durF != 0 else 0
            marker(f"BENCHMARK:vs_zepto_{test_name}_ratio:{ratio:.3f}")
        else:
            marker(f"TEST_FAIL:{test_name}:{res.stderr.strip()}")
        marker(f"BENCHMARK:{test_name}_total_ms:{total*1000:.2f}")
    finally:
        httpd.shutdown()
        httpd.server_close()

    # Additional generic benchmarks
    # Memory snapshot
    tracemalloc.start()
    time.sleep(0.1)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    marker(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
    marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

    # Final marker
    marker("RUN_OK")

if __name__ == "__main__":
    run()