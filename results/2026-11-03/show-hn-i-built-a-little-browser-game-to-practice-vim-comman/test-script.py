import subprocess, sys, time, json, traceback, os, tracemalloc
import urllib.request

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk():
    start = time.time()
    result = run_cmd(['apk', 'add', '--no-cache', 'nodejs', 'npm'])
    elapsed = time.time() - start
    if result and result.returncode == 0:
        print_marker(f"INSTALL_OK")
    else:
        reason = (result.stderr.strip() if result else str(e))
        print_marker(f"INSTALL_FAIL:{reason}")
    print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.3f}")

def install_app():
    # clone repo (fallback) and npm install
    repo_url = "https://github.com/duy/hjkl.git"
    workdir = "/tmp/hjkl"
    if os.path.isdir(workdir):
        subprocess.run(['rm', '-rf', workdir])
    start = time.time()
    clone = run_cmd(['git', 'clone', '--depth', '1', repo_url, workdir])
    if not clone or clone.returncode != 0:
        print_marker(f"INSTALL_FAIL:git_clone_failed")
        return None
    os.chdir(workdir)
    npm_install = run_cmd(['npm', 'install', '--omit=dev'])
    elapsed = time.time() - start
    if npm_install and npm_install.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = npm_install.stderr.strip() if npm_install else "npm_install_error"
        print_marker(f"INSTALL_FAIL:{reason}")
    print_marker(f"BENCHMARK:npm_install_time_s:{elapsed:.3f}")
    # start server in background
    server_cmd = ['npm', 'start']
    server = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # give it time to start
    time.sleep(5)
    return server

def http_get(url, timeout=10):
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read().decode('utf-8', errors='ignore')
        elapsed = time.time() - start
        return data, elapsed, None
    except Exception as e:
        return None, None, str(e)

def test_load_page():
    try:
        data, elapsed, err = http_get("http://localhost:3000/")
        if err:
            raise Exception(err)
        if "Start" in data or "start" in data.lower():
            print_marker("TEST_PASS:load_start_screen")
        else:
            raise Exception("Start screen text not found")
        print_marker(f"BENCHMARK:page_load_time_ms:{elapsed*1000:.2f}")
        # baseline 2000 ms
        ratio = elapsed*1000 / 2000.0
        print_marker(f"BENCHMARK:vs_vim_adventures_load_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:load_start_screen:{e}")

def test_health_endpoint():
    try:
        data, elapsed, err = http_get("http://localhost:3000/health")
        if err:
            raise Exception(err)
        if data and ("ok" in data.lower() or "healthy" in data.lower()):
            print_marker("TEST_PASS:health_endpoint")
        else:
            raise Exception("Health check response unexpected")
        print_marker(f"BENCHMARK:health_check_time_ms:{elapsed*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:health_endpoint:{e}")

def main():
    tracemalloc.start()
    install_apk()
    server = install_app()
    if not server:
        print_marker("TEST_SKIP:run_server:server_start_failed")
    else:
        test_load_page()
        test_health_endpoint()
        # clean up server
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()
    current, peak = tracemalloc.get_traced_memory()
    print_marker(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()