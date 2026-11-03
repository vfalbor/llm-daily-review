import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(pkgs):
    start = time.time()
    try:
        res = subprocess.run(['apk', 'add', '--no-cache'] + pkgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker(f"INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    finally:
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.2f}")

def clone_repo(url, dest):
    if dest.exists():
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', url, str(dest)])
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())

def cargo_build(path):
    start = time.time()
    res = run_cmd(['cargo', 'build', '--release'], cwd=str(path))
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:cargo_build_time_s:{elapsed:.2f}")

def measure_import_time(module_name):
    start = time.time()
    try:
        __import__(module_name)
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:import_{module_name}_ms:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")

def bench_baseline_dd():
    # simple dd copy from /dev/zero to /dev/null 1M bytes
    start = time.time()
    res = run_cmd(['dd', 'if=/dev/zero', 'of=/dev/null', 'bs=1M', 'count=10'])
    elapsed = (time.time() - start) * 1000
    print_marker(f"BENCHMARK:dd_10M_copy_ms:{elapsed:.2f}")
    return elapsed

def bench_vs_baseline(metric_name, our_val, baseline_val):
    try:
        ratio = our_val / baseline_val if baseline_val != 0 else float('inf')
        print_marker(f"BENCHMARK:vs_dd_{metric_name}:{ratio:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:vs_dd_{metric_name}:{e}")

def test_help(exec_path):
    start = time.time()
    try:
        res = run_cmd([exec_path, '--help'])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker("TEST_PASS:help")
    except Exception as e:
        print_marker(f"TEST_FAIL:help:{e}")
    finally:
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:help_time_ms:{elapsed:.2f}")

def test_version(exec_path):
    start = time.time()
    try:
        res = run_cmd([exec_path, '--version'])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker("TEST_PASS:version")
    except Exception as e:
        print_marker(f"TEST_FAIL:version:{e}")
    finally:
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:version_time_ms:{elapsed:.2f}")

def main():
    # 1. Install required apk packages
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])

    # 2. Clone and build DiscImageStudio
    repo_url = "https://github.com/JiaFeiMiao-K-Cat/DiscImageStudio.git"
    src_dir = pathlib.Path("/tmp/DiscImageStudio")
    try:
        start = time.time()
        clone_repo(repo_url, src_dir)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:clone:{e}")
    finally:
        print_marker(f"BENCHMARK:git_clone_time_s:{time.time() - start:.2f}")

    try:
        cargo_build(src_dir)
        exec_path = str(src_dir / "target" / "release" / "DiscImageStudio")
        if not os.path.isfile(exec_path):
            raise FileNotFoundError(f"Executable not found at {exec_path}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:build:{e}")
        exec_path = None

    # 3. Run tests if build succeeded
    if exec_path:
        test_help(exec_path)
        test_version(exec_path)
    else:
        print_marker("TEST_SKIP:help:binary not built")
        print_marker("TEST_SKIP:version:binary not built")

    # 4. Benchmark baseline tool (dd)
    baseline_ms = bench_baseline_dd()

    # 5. Compare help benchmark against baseline (just as example)
    # Collect our help benchmark from earlier printed line via simple parsing is not feasible here,
    # so we re‑measure quickly for comparison.
    if exec_path:
        start = time.time()
        run_cmd([exec_path, '--help'])
        our_help_ms = (time.time() - start) * 1000
        bench_vs_baseline("help_time", our_help_ms, baseline_ms)

    # 6. Additional simple memory benchmark using tracemalloc
    tracemalloc.start()
    dummy = [i for i in range(1000000)]
    current, peak = tracemalloc.get_traced_memory()
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    tracemalloc.stop()

    # 7. Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()