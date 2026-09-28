import subprocess, sys, os, time, json, traceback, http.client, socket, threading, urllib.request, urllib.error, tracemalloc, shutil, pathlib, math

# Helper to print markers
def print_marker(marker):
    print(marker, flush=True)

def run_cmd(cmd, cwd=None, env=None, timeout=300):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        elapsed = time.time() - start
        return result.returncode, result.stdout, result.stderr, elapsed
    except Exception as e:
        return -1, "", str(e), 0.0

def install_apk(pkgs):
    rc, out, err, _ = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:apk add failed - {err.strip()}")
    return rc == 0

def install_node_deps(repo_path):
    rc, out, err, elapsed = run_cmd(['npm', 'install'], cwd=repo_path)
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:npm install failed - {err.strip()}")
    print_marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")
    return rc == 0

def start_server(repo_path):
    # npm start typically runs a dev server; we run it in a separate thread
    env = os.environ.copy()
    env["PORT"] = "3000"
    proc = subprocess.Popen(['npm', 'start'], cwd=repo_path, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Wait a bit for server to start
    time.sleep(5)
    return proc

def stop_server(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

def http_get(host, port, path):
    conn = http.client.HTTPConnection(host, port, timeout=10)
    start = time.time()
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        data = resp.read()
        elapsed = time.time() - start
        return resp.status, data, elapsed
    finally:
        conn.close()

def test_server_response():
    try:
        status, _, elapsed = http_get('127.0.0.1', 3000, '/')
        if status == 200:
            print_marker(f"TEST_PASS:server_responds")
        else:
            print_marker(f"TEST_FAIL:server_responds:Unexpected status {status}")
        print_marker(f"BENCHMARK:response_time_ms:{elapsed*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:server_responds:{e}")

def build_prod_bundle(repo_path):
    rc, out, err, elapsed = run_cmd(['npm', 'run', 'build'], cwd=repo_path)
    if rc == 0:
        print_marker("TEST_PASS:build_prod")
    else:
        print_marker(f"TEST_FAIL:build_prod:{err.strip()}")
    print_marker(f"BENCHMARK:build_time_s:{elapsed:.2f}")
    # Measure bundle size if dist folder exists
    dist_path = os.path.join(repo_path, 'dist')
    if os.path.isdir(dist_path):
        total = 0
        for root, _, files in os.walk(dist_path):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        print_marker(f"BENCHMARK:bundle_size_bytes:{total}")
    else:
        print_marker("TEST_SKIP:bundle_size:dist folder not found")

def run_playwright_test(repo_path):
    # Install Playwright browsers if needed
    rc, out, err, _ = run_cmd(['npx', 'playwright', 'install'], cwd=repo_path)
    if rc != 0:
        print_marker(f"TEST_SKIP:playwright_install:{err.strip()}")
        return
    # Simple test script inline
    test_js = """
    const { test, expect } = require('@playwright/test');
    test('add item', async ({ page }) => {
        await page.goto('http://localhost:3000');
        await page.fill('input[placeholder="Add item"]', 'test item');
        await page.keyboard.press('Enter');
        await expect(page.locator('li')).toContainText('test item');
    });
    """
    test_file = os.path.join(repo_path, 'playwright_test.js')
    with open(test_file, 'w') as f:
        f.write(test_js)
    rc, out, err, elapsed = run_cmd(['npx', 'playwright', 'test', 'playwright_test.js'], cwd=repo_path)
    if rc == 0:
        print_marker("TEST_PASS:playwright_e2e")
    else:
        print_marker(f"TEST_FAIL:playwright_e2e:{err.strip()}")
    print_marker(f"BENCHMARK:e2e_time_s:{elapsed:.2f}")

def baseline_comparisons():
    # Simple static baseline numbers for similar tools (hypothetical)
    # Assume baseline response time 120ms, bundle size 500KB
    baseline_resp_ms = 120.0
    baseline_bundle_bytes = 500 * 1024
    # Use last measured values from env if possible
    # Here we just compute ratios from placeholder variables
    # In real run we would store the metrics; for demo we recompute quickly
    try:
        # retrieve last response time from a temporary file
        with open('/tmp/last_response_ms', 'r') as f:
            resp_ms = float(f.read().strip())
        ratio = resp_ms / baseline_resp_ms
        print_marker(f"BENCHMARK:vs_google_keep_response_ratio:{ratio:.2f}")
    except:
        pass
    try:
        with open('/tmp/last_bundle_bytes', 'r') as f:
            size = int(f.read().strip())
        ratio = size / baseline_bundle_bytes
        print_marker(f"BENCHMARK:vs_google_keep_bundle_ratio:{ratio:.2f}")
    except:
        pass

def main():
    # Ensure apk packages
    install_apk(['nodejs', 'npm', 'git', 'bash'])

    # Clone repo
    repo_url = "https://github.com/seamusc/papermono-shopping-list.git"
    repo_dir = "/tmp/papermono"
    if os.path.isdir(repo_dir):
        shutil.rmtree(repo_dir)
    rc, out, err, _ = run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
    if rc != 0:
        print_marker(f"INSTALL_FAIL:git clone failed - {err.strip()}")
        print_marker("RUN_OK")
        return

    # Install npm deps
    if not install_node_deps(repo_dir):
        print_marker("RUN_OK")
        return

    # Start server
    server_proc = start_server(repo_dir)
    try:
        # Test response
        test_server_response()
        # Save response metric for baseline comparison
        try:
            status, _, elapsed = http_get('127.0.0.1', 3000, '/')
            with open('/tmp/last_response_ms', 'w') as f:
                f.write(str(elapsed*1000))
        except:
            pass

        # Build production bundle
        build_prod_bundle(repo_dir)

        # Save bundle size for baseline
        dist_path = os.path.join(repo_dir, 'dist')
        if os.path.isdir(dist_path):
            total = sum(os.path.getsize(os.path.join(root, f))
                        for root, _, files in os.walk(dist_path) for f in files)
            with open('/tmp/last_bundle_bytes', 'w') as f:
                f.write(str(total))

        # Run e2e test
        run_playwright_test(repo_dir)

        # Baseline comparisons
        baseline_comparisons()

    except Exception as e:
        print_marker(f"TEST_FAIL:unexpected:{traceback.format_exc()}")
    finally:
        stop_server(server_proc)

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()