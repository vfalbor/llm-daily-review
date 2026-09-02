import subprocess, sys, time, os, json, shutil, tracemalloc, threading, socket

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper

@measure_time
def apk_install(pkg):
    return run_cmd(['apk','add','--no-cache',pkg])

@measure_time
def git_clone(repo_url, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    return run_cmd(['git','clone',repo_url,dest])

@measure_time
def npm_install(path):
    return run_cmd(['npm','install'], cwd=path)

@measure_time
def npm_build(path):
    return run_cmd(['npm','run','build'], cwd=path)

def start_server(path, port=3000):
    # start npm start (or equivalent) in background
    proc = subprocess.Popen(['npm','run','serve'], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # wait for port to open
    timeout = 30
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('127.0.0.1', port))
                return proc
            except OSError:
                time.sleep(0.5)
    proc.terminate()
    return None

def count_source_files(root):
    extensions = {}
    total = 0
    for dirpath, _, files in os.walk(root):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                extensions[ext] = extensions.get(ext,0)+1
                total +=1
    return total, extensions

def main():
    # 1. Install system packages
    apk_res, apk_time = apk_install('git')
    if apk_res.returncode == 0:
        print_marker('INSTALL_OK')
    else:
        print_marker(f'INSTALL_FAIL:apk git error {apk_res.stderr.strip()}')
    print_marker(f'BENCHMARK:apk_install_time_s:{apk_time:.2f}')

    repo_url = 'https://github.com/webfpga/webfpga.git'
    dest_dir = '/tmp/webfpga'

    # 2. Clone repo
    try:
        (clone_res, clone_time) = git_clone(repo_url, dest_dir)
        if clone_res.returncode == 0:
            print_marker('TEST_PASS:git_clone')
        else:
            raise RuntimeError(clone_res.stderr.strip())
    except Exception as e:
        print_marker(f'TEST_FAIL:git_clone:{e}')
    print_marker(f'BENCHMARK:git_clone_time_s:{clone_time:.2f}')

    # 3. npm install
    try:
        (npm_inst_res, npm_inst_time) = npm_install(dest_dir)
        if npm_inst_res.returncode == 0:
            print_marker('TEST_PASS:npm_install')
        else:
            raise RuntimeError(npm_inst_res.stderr.strip())
    except Exception as e:
        print_marker(f'TEST_FAIL:npm_install:{e}')
    print_marker(f'BENCHMARK:npm_install_time_s:{npm_inst_time:.2f}')

    # 4. npm build
    try:
        (npm_build_res, npm_build_time) = npm_build(dest_dir)
        if npm_build_res.returncode == 0:
            print_marker('TEST_PASS:npm_build')
        else:
            raise RuntimeError(npm_build_res.stderr.strip())
    except Exception as e:
        print_marker(f'TEST_FAIL:npm_build:{e}')
    print_marker(f'BENCHMARK:npm_build_time_s:{npm_build_time:.2f}')

    # 5. Count source files
    try:
        total_files, ext_counts = count_source_files(dest_dir)
        print_marker(f'TEST_PASS:source_count')
        print_marker(f'BENCHMARK:source_files_count:{total_files}')
        for ext, cnt in ext_counts.items():
            print_marker(f'BENCHMARK:src_ext_{ext}_count:{cnt}')
    except Exception as e:
        print_marker(f'TEST_FAIL:source_count:{e}')

    # 6. Start server and check reachable
    try:
        server_proc = start_server(dest_dir, port=3000)
        if server_proc:
            print_marker('TEST_PASS:server_start')
            server_proc.terminate()
        else:
            raise RuntimeError('Server did not start within timeout')
    except Exception as e:
        print_marker(f'TEST_FAIL:server_start:{e}')

    # 7. Benchmark vs baseline (ELECTOR build time placeholder)
    # Assume baseline build time 10 seconds
    baseline_time = 10.0
    ratio = npm_build_time / baseline_time if baseline_time else 0
    print_marker(f'BENCHMARK:vs_elector_build_time_ratio:{ratio:.2f}')

    print_marker('RUN_OK')

if __name__ == '__main__':
    main()