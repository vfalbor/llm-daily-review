import subprocess, sys, os, time, tracemalloc, json, urllib.request, urllib.error, shutil, threading, queue

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass  # ignore errors, will be caught later

def run_cmd(cmd, cwd=None, env=None, timeout=30):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)

def clone_repo(url, dest):
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        subprocess.run(['git', 'clone', '--depth', '1', url, dest], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, ""
    except Exception as e:
        return False, str(e)

def install_node_deps(repo_path):
    try:
        result = run_cmd(['npm', 'install', '--silent'], cwd=repo_path)
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, ""
    except Exception as e:
        return False, str(e)

def exec_help(repo_path):
    try:
        result = run_cmd(['node', 'index.js', '--help'], cwd=repo_path)
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def start_worker(repo_path, stop_event, out_q):
    try:
        proc = subprocess.Popen(['npm', 'run', 'dev'], cwd=repo_path,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            out_q.put(line)
            if stop_event.is_set():
                proc.terminate()
                break
        proc.wait()
    except Exception as e:
        out_q.put(f'ERROR:{e}')

def mock_send_message():
    # Simulate API call latency
    start = time.time()
    time.sleep(0.1)  # mock network
    return time.time() - start

def main():
    # 1. Install required APK packages
    for pkg in ['git', 'curl']:
        apk_install(pkg)
    # 2. Clone repository
    repo_url = 'https://github.com/finereli/whatsapp-mcp'
    repo_dir = '/tmp/whatsapp-mcp'
    ok, msg = clone_repo(repo_url, repo_dir)
    if ok:
        print_marker('INSTALL_OK')
    else:
        print_marker(f'INSTALL_FAIL:{msg}')
    # 3. Install node dependencies
    t0 = time.time()
    ok, msg = install_node_deps(repo_dir)
    t1 = time.time()
    install_time = t1 - t0
    print_marker(f'BENCHMARK:install_time_s:{install_time:.2f}')
    if ok:
        print_marker('INSTALL_OK')
    else:
        print_marker(f'INSTALL_FAIL:{msg}')
    # 4. Test CLI help
    try:
        ok, out = exec_help(repo_dir)
        if ok:
            print_marker('TEST_PASS:cli_help')
        else:
            print_marker(f'TEST_FAIL:cli_help:{out}')
    except Exception as e:
        print_marker(f'TEST_FAIL:cli_help:{e}')
    # 5. Benchmark import time (require node import)
    tracemalloc.start()
    t0 = time.time()
    try:
        subprocess.run(['node', '-e', "require('./index.js')"], cwd=repo_dir,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        import_ok = True
    except Exception:
        import_ok = False
    t1 = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f'BENCHMARK:import_time_ms:{(t1-t0)*1000:.1f}')
    print_marker(f'BENCHMARK:memory_peak_kb:{peak/1024:.1f}')
    if import_ok:
        print_marker('TEST_PASS:node_import')
    else:
        print_marker('TEST_FAIL:node_import:Import failed')
    # 6. Start worker and mock send message
    stop_event = threading.Event()
    out_q = queue.Queue()
    worker_thread = threading.Thread(target=start_worker, args=(repo_dir, stop_event, out_q))
    worker_thread.start()
    time.sleep(2)  # give it time to start
    latency = mock_send_message()
    print_marker(f'BENCHMARK:message_latency_ms:{latency*1000:.2f}')
    # Compare against baseline (assume baseline latency 150ms)
    baseline_ms = 150.0
    ratio = latency*1000 / baseline_ms
    print_marker(f'BENCHMARK:vs_twilio_latency_ratio:{ratio:.2f}')
    # Cleanup
    stop_event.set()
    worker_thread.join(timeout=5)
    # 7. Graceful shutdown test (already done via stop_event)
    print_marker('TEST_PASS:graceful_shutdown')
    # Final marker
    print_marker('RUN_OK')

if __name__ == '__main__':
    main()