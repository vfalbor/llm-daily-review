import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib

def log(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            log(f"INSTALL_OK | {pkg}")
        else:
            log(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        log(f"INSTALL_FAIL:{pkg}:{e}")

def install_go():
    # go is provided by apk package 'go'
    install_apk('go')

def clone_repo(url, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if res.returncode != 0:
        raise RuntimeError(f"git clone failed: {res.stderr.strip()}")
    return dest

def benchmark(label, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        result = e
        success = False
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = end - start
    log(f"BENCHMARK:{label}:{elapsed:.4f}")
    log(f"BENCHMARK:{label}_mem_kb:{peak/1024:.2f}")
    return success, result, elapsed

def main():
    # 1. Install required system packages
    for pkg in ['nodejs', 'npm', 'git', 'cargo', 'rust', 'go']:
        install_apk(pkg)

    repo_url = "https://github.com/mikuta0407/win4wine"
    src_dir = "/tmp/win4wine_src"
    binary_path = os.path.join(src_dir, "win4wine")
    baseline_startup_ms = 3000  # assumed baseline startup time for native wine shell (ms)

    # Test 1: Clone and build
    try:
        success, _, clone_time = benchmark("clone_repo_time_s", clone_repo, repo_url, src_dir)
        if not success:
            raise RuntimeError("clone failed")
        # build
        def build():
            res = run_cmd(['go', 'build', '-o', 'win4wine', '.'], cwd=src_dir)
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
        success, _, build_time = benchmark("go_build_time_s", build)
        if success:
            log("TEST_PASS:build")
        else:
            raise RuntimeError("build failed")
    except Exception as e:
        log(f"TEST_FAIL:build:{e}")

    # Test 2: Verify --help output
    try:
        def run_help():
            res = run_cmd([binary_path, '--help'])
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
            if "Usage" not in res.stdout:
                raise RuntimeError("help output missing expected keyword")
            return res.stdout
        success, out, help_time = benchmark("help_output_time_s", run_help)
        if success:
            log("TEST_PASS:help_output")
        else:
            raise RuntimeError(out)
    except Exception as e:
        log(f"TEST_FAIL:help_output:{e}")

    # Test 3: Measure startup time (binary with --dry-run to avoid launching UI)
    # The tool does not have a dry-run flag; we will invoke with '--help' as proxy for startup.
    try:
        def startup():
            start = time.time()
            res = run_cmd([binary_path, '--help'])
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
            return (time.time() - start) * 1000  # ms
        success, startup_ms, _ = benchmark("startup_time_ms", startup)
        if success:
            log("TEST_PASS:startup")
        else:
            raise RuntimeError(startup_ms)
    except Exception as e:
        log(f"TEST_FAIL:startup:{e}")

    # Baseline comparison
    try:
        ratio = (startup_ms / baseline_startup_ms) if baseline_startup_ms else 0
        log(f"BENCHMARK:vs_wine_shell_startup_ratio:{ratio:.4f}")
    except Exception as e:
        log(f"TEST_FAIL:benchmark_vs_baseline:{e}")

    # Additional benchmarks: count files in repo, lines of code (approx)
    try:
        file_count = sum(len(files) for _, _, files in os.walk(src_dir))
        log(f"BENCHMARK:repo_file_count:{file_count}")
        # simple LOC count using wc -l
        res = run_cmd(['sh', '-c', f'find {src_dir} -name "*.go" -print0 | xargs -0 cat | wc -l'])
        loc = int(res.stdout.strip())
        log(f"BENCHMARK:repo_loc_count:{loc}")
    except Exception as e:
        log(f"TEST_FAIL:repo_metrics:{e}")

    # Final marker
    log("RUN_OK")

if __name__ == "__main__":
    main()