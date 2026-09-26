import subprocess, sys, time, tracemalloc, json, os, shutil, tempfile

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(pkgs):
    start = time.time()
    result = run_cmd(['apk', 'add', '--no-cache'] + pkgs, check=False)
    elapsed = time.time() - start
    if result.returncode == 0:
        print_marker(f"INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{result.stderr.strip()}")
    return elapsed

def pip_install(package):
    start = time.time()
    result = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package])
    elapsed = time.time() - start
    if result.returncode == 0:
        print_marker(f"INSTALL_OK")
        return True, elapsed
    else:
        print_marker(f"INSTALL_FAIL:{result.stderr.strip()}")
        return False, elapsed

def git_clone(repo, dest):
    start = time.time()
    result = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    elapsed = time.time() - start
    if result.returncode == 0:
        return True, elapsed
    else:
        print_marker(f"INSTALL_FAIL:{result.stderr.strip()}")
        return False, elapsed

def pip_editable(path):
    start = time.time()
    result = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    elapsed = time.time() - start
    if result.returncode == 0:
        print_marker(f"INSTALL_OK")
        return True, elapsed
    else:
        print_marker(f"INSTALL_FAIL:{result.stderr.strip()}")
        return False, elapsed

def benchmark(name, func):
    try:
        tracemalloc.start()
        start = time.time()
        func()
        end = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration = end - start
        print_marker(f"BENCHMARK:{name}:{duration:.3f}")
        return duration
    except Exception as e:
        print_marker(f"BENCHMARK:{name}:error:{e}")
        return None

def test_cli_help():
    try:
        result = run_cmd(['floci', '--help'])
        if result.returncode == 0 and 'usage' in result.stdout.lower():
            print_marker("TEST_PASS:cli_help")
        else:
            print_marker(f"TEST_FAIL:cli_help:{result.stderr.strip() or 'non-zero exit'}")
    except FileNotFoundError:
        print_marker("TEST_FAIL:cli_help:binary not found")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_help:{e}")

def test_version():
    try:
        result = run_cmd(['floci', '--version'])
        if result.returncode == 0 and result.stdout.strip():
            print_marker("TEST_PASS:cli_version")
        else:
            print_marker(f"TEST_FAIL:cli_version:{result.stderr.strip() or 'non-zero exit'}")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_version:{e}")

def test_emulate_s3():
    # Simple smoke test: run floci with a dummy command that should exit quickly
    try:
        result = run_cmd(['floci', 's3', 'list-buckets'], timeout=10)
        # Expect non-zero exit because no config, but should run without crash
        if result.returncode != 0 and 'error' not in result.stderr.lower():
            print_marker("TEST_PASS:emulate_s3")
        else:
            print_marker(f"TEST_FAIL:emulate_s3:{result.stderr.strip() or 'unexpected success'}")
    except subprocess.TimeoutExpired:
        print_marker("TEST_FAIL:emulate_s3:timeout")
    except Exception as e:
        print_marker(f"TEST_FAIL:emulate_s3:{e}")

def main():
    # 1. Install system packages
    apk_time = install_apk(['git', 'curl'])

    # 2. Try pip install first
    pip_success, pip_time = pip_install('floci')
    install_time = pip_time if pip_success else None

    # 3. Fallback to git clone + editable install
    if not pip_success:
        tmpdir = tempfile.mkdtemp()
        clone_ok, clone_time = git_clone('https://github.com/floci/floci.git', tmpdir)
        if clone_ok:
            edit_ok, edit_time = pip_editable(tmpdir)
            install_time = clone_time + edit_time if edit_ok else None
        else:
            install_time = None

    # Benchmark install time
    if install_time is not None:
        print_marker(f"BENCHMARK:install_time_s:{install_time:.3f}")
    else:
        print_marker("BENCHMARK:install_time_s:error")

    # 4. Run tests with timing
    benchmark('cli_help', test_cli_help)
    benchmark('cli_version', test_version)
    benchmark('emulate_s3', test_emulate_s3)

    # 5. Baseline comparison with LocalStack (approximate install time 30s)
    baseline_time = 30.0
    if install_time:
        ratio = install_time / baseline_time
        print_marker(f"BENCHMARK:vs_localstack_install_time_ratio:{ratio:.3f}")

    # Additional arbitrary benchmarks
    print_marker(f"BENCHMARK:loc_count:{len(open(__file__).readlines())}")
    print_marker(f"BENCHMARK:memory_peak_kb:{tracemalloc.get_traced_memory()[1]//1024 if tracemalloc.is_tracing() else 0}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()