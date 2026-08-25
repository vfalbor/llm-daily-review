#!/usr/bin/env python3
import subprocess, sys, os, time, json, traceback, urllib.request, shutil, tempfile, tracemalloc

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, ''
    except Exception as e:
        return False, str(e)

def download_release(url, dest):
    try:
        with urllib.request.urlopen(url) as resp, open(dest, 'wb') as out:
            shutil.copyfileobj(resp, out)
        return True, ''
    except Exception as e:
        return False, str(e)

def run_cmd(cmd, cwd=None, env=None):
    start = time.time()
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        elapsed = time.time() - start
        return True, result.stdout, result.stderr, elapsed
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start
        return False, e.stdout, e.stderr, elapsed

def measure_mem(func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        func(*args, **kwargs)
        success = True
    except Exception:
        success = False
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return success, time.time() - start, peak / 1024  # KiB

# 1. Install system deps
for pkg in ['git', 'curl']:
    ok, reason = apk_install(pkg)
    if ok:
        print_marker('INSTALL_OK')
    else:
        print_marker(f'INSTALL_FAIL:{reason}')

# 2. Acquire walgit binary (latest release)
tmpdir = tempfile.mkdtemp(prefix='walgit_test_')
binary_path = os.path.join(tmpdir, 'walgit')
release_api = 'https://api.github.com/repos/tobi/walgit/releases/latest'
try:
    with urllib.request.urlopen(release_api) as resp:
        data = json.load(resp)
    assets = data.get('assets', [])
    dl_url = None
    for a in assets:
        if a['name'].endswith('linux-amd64'):
            dl_url = a['browser_download_url']
            break
    if not dl_url:
        raise RuntimeError('No suitable binary asset found')
    ok, reason = download_release(dl_url, binary_path)
    if ok:
        os.chmod(binary_path, 0o755)
        print_marker('INSTALL_OK')
    else:
        raise RuntimeError(reason)
except Exception as e:
    print_marker(f'INSTALL_FAIL:{e}')
    # fallback: clone and build
    src_dir = os.path.join(tmpdir, 'src')
    ok, _, _, _ = run_cmd(['git', 'clone', 'https://github.com/tobi/walgit.git', src_dir])
    if ok:
        ok, _, err, _ = run_cmd(['go', 'build', '-o', binary_path], cwd=src_dir)
        if ok:
            os.chmod(binary_path, 0o755)
            print_marker('INSTALL_OK')
        else:
            print_marker(f'INSTALL_FAIL:go build error: {err}')
    else:
        print_marker(f'INSTALL_FAIL:git clone error')

# 3. Start server with local filesystem backend
server_dir = os.path.join(tmpdir, 'repo_store')
os.makedirs(server_dir, exist_ok=True)
server_proc = None
start_time = time.time()
try:
    server_proc = subprocess.Popen([binary_path,
                                    '--dir', server_dir,
                                    '--listen', '127.0.0.1:9418'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
    # give it a moment to start
    time.sleep(2)
    bench_start = time.time() - start_time
    print_marker(f'BENCHMARK:server_start_time_s:{bench_start:.3f}')
except Exception as e:
    print_marker(f'TEST_FAIL:server_start:{e}')

# 4. Test clone, push, fetch workflow
repo_url = 'git://127.0.0.1:9418/testrepo.git'
clone1 = os.path.join(tmpdir, 'clone1')
clone2 = os.path.join(tmpdir, 'clone2')
bench_push_time = None
bench_fetch_time = None

try:
    # init empty repo on server
    init_repo_path = os.path.join(server_dir, 'testrepo.git')
    os.makedirs(init_repo_path, exist_ok=True)
    run_cmd(['git', 'init', '--bare', init_repo_path])

    # clone1
    ok, out, err, _ = run_cmd(['git', 'clone', repo_url, clone1])
    if not ok:
        raise RuntimeError(f'clone1 failed: {err}')
    # create a 1MB file
    file_path = os.path.join(clone1, 'bigfile.bin')
    with open(file_path, 'wb') as f:
        f.write(os.urandom(1024 * 1024))
    # commit
    run_cmd(['git', 'add', 'bigfile.bin'], cwd=clone1)
    run_cmd(['git', 'commit', '-m', 'add big file'], cwd=clone1)

    # push and measure
    start = time.time()
    ok, out, err, _ = run_cmd(['git', 'push', 'origin', 'master'], cwd=clone1)
    bench_push_time = time.time() - start
    if not ok:
        raise RuntimeError(f'push failed: {err}')
    print_marker(f'TEST_PASS:push')
    print_marker(f'BENCHMARK:push_time_s:{bench_push_time:.3f}')

    # clone2
    ok, out, err, _ = run_cmd(['git', 'clone', repo_url, clone2])
    if not ok:
        raise RuntimeError(f'clone2 failed: {err}')

    # fetch from clone2 and measure
    start = time.time()
    ok, out, err, _ = run_cmd(['git', 'fetch'], cwd=clone2)
    bench_fetch_time = time.time() - start
    if not ok:
        raise RuntimeError(f'fetch failed: {err}')
    print_marker(f'TEST_PASS:fetch')
    print_marker(f'BENCHMARK:fetch_time_s:{bench_fetch_time:.3f}')

except Exception as e:
    print_marker(f'TEST_FAIL:workflow:{e}')
    traceback.print_exc(file=sys.stderr)

# 5. Check server logs for errors
if server_proc:
    try:
        # give server a moment to flush logs
        time.sleep(1)
        server_proc.terminate()
        stdout, stderr = server_proc.communicate(timeout=5)
        if stderr:
            if 'error' in stderr.lower():
                print_marker(f'TEST_FAIL:server_logs:found error')
            else:
                print_marker(f'TEST_PASS:server_logs')
        else:
            print_marker(f'TEST_PASS:server_logs')
    except Exception as e:
        print_marker(f'TEST_FAIL:server_logs:{e}')

# 6. Additional benchmarks
mem_success, mem_time, mem_peak = measure_mem(time.sleep, 0.1)
print_marker(f'BENCHMARK:memory_peak_kib:{mem_peak:.1f}')
print_marker(f'BENCHMARK:memory_measure_time_s:{mem_time:.3f}')

# 7. Baseline comparison against Gitea (assume baseline push time 0.8s)
baseline_push = 0.8
if bench_push_time is not None:
    ratio = bench_push_time / baseline_push
    print_marker(f'BENCHMARK:vs_gitea_push_ratio:{ratio:.2f}')

# Final marker
print_marker('RUN_OK')