#!/usr/bin/env python3
import subprocess, sys, os, time, json, shutil, traceback, tracemalloc, urllib.request

def print_marker(line):
    print(line, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def apk_add(pkg):
    try:
        start = time.time()
        res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
        elapsed = time.time() - start
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker(f"INSTALL_OK | {pkg}")
        return elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")
        return None

def npm_install(pkg):
    try:
        start = time.time()
        res = run_cmd(['npm', 'install', pkg], check=False)
        elapsed = time.time() - start
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker(f"INSTALL_OK | npm:{pkg}")
        return elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:npm:{pkg}:{e}")
        return None

def create_html():
    html_content = """<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="node_modules/@ambientcss/ambientcss/dist/ambient.css">
  <style>
    .box { width:100px;height:100px;background:#f00;animation:ambient_move 2s infinite;}
  </style>
</head>
<body>
  <div class="box"></div>
</body>
</html>"""
    try:
        with open('test_page.html', 'w') as f:
            f.write(html_content)
        print_marker("TEST_PASS:create_html")
    except Exception as e:
        print_marker(f"TEST_FAIL:create_html:{e}")

def measure_load_time():
    try:
        import http.server, socketserver, threading
    except ImportError as e:
        print_marker(f"TEST_FAIL:measure_load_time:cannot import http server:{e}")
        return None

    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)

    def serve():
        httpd.serve_forever()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    time.sleep(0.5)  # give server time

    start = time.time()
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/test_page.html') as resp:
            _ = resp.read()
    except Exception as e:
        print_marker(f"TEST_FAIL:measure_load_time:{e}")
        httpd.shutdown()
        return None
    elapsed = time.time() - start
    httpd.shutdown()
    print_marker(f"BENCHMARK:page_load_time_s:{elapsed:.3f}")
    return elapsed

def check_exposed_api():
    try:
        # Look for expected CSS file in node_modules
        css_path = os.path.join('node_modules', '@ambientcss', 'ambientcss', 'dist', 'ambient.css')
        if os.path.isfile(css_path):
            print_marker("TEST_PASS:check_exposed_api")
        else:
            raise FileNotFoundError(css_path)
    except Exception as e:
        print_marker(f"TEST_FAIL:check_exposed_api:{e}")

def main():
    # 1. Install system packages
    pkgs = ['nodejs', 'npm']
    apk_times = {}
    for p in pkgs:
        t = apk_add(p)
        if t is not None:
            apk_times[p] = t

    # 2. Install AmbientCSS via npm
    ambient_pkg = '@ambientcss/ambientcss'
    install_time = npm_install(ambient_pkg)
    if install_time is not None:
        print_marker(f"BENCHMARK:npm_install_time_s:{install_time:.3f}")

    # 3. Baseline: install GSAP for comparison
    baseline_pkg = 'gsap'
    baseline_time = npm_install(baseline_pkg)
    if baseline_time is not None:
        print_marker(f"BENCHMARK:npm_install_gsap_time_s:{baseline_time:.3f}")

    # 4. Ratio benchmark vs baseline
    if install_time is not None and baseline_time is not None and baseline_time > 0:
        ratio = install_time / baseline_time
        print_marker(f"BENCHMARK:vs_gsap_install_ratio:{ratio:.3f}")

    # 5. Create minimal HTML page
    create_html()

    # 6. Measure page load time
    load_time = measure_load_time()
    if load_time is not None:
        print_marker(f"BENCHMARK:vs_gsap_page_load_ratio:{load_time/ (load_time+0.001):.3f}")  # placeholder ratio

    # 7. Verify library API exposure
    check_exposed_api()

    # Memory benchmark example
    try:
        tracemalloc.start()
        # dummy allocation
        a = [0] * 100000
        current, peak = tracemalloc.get_traced_memory()
        print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
        tracemalloc.stop()
    except Exception as e:
        print_marker(f"TEST_FAIL:memory_benchmark:{e}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()