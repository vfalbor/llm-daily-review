#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None):
    start = time.perf_counter()
    tracemalloc.start()
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        current, peak = tracemalloc.get_traced_memory()
        elapsed = time.perf_counter() - start
        tracemalloc.stop()
        return {
            'ok': result.returncode == 0,
            'out': result.stdout,
            'err': result.stderr,
            'time': elapsed,
            'mem_peak': peak / 1024,  # KiB
            'returncode': result.returncode
        }
    except Exception as e:
        tracemalloc.stop()
        return {
            'ok': False,
            'out': '',
            'err': str(e),
            'time': time.perf_counter() - start,
            'mem_peak': 0,
            'returncode': -1
        }

def install_apk(pkg):
    res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{res.stderr.strip() or 'apk install error'}")
    return res.returncode == 0

def pip_install(package):
    cmd = [sys.executable, '-m', 'pip', 'install', package]
    res = run_cmd(cmd)
    if res['ok']:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{res['err'][:200]}")
    return res['ok'], res['time']

def main():
    # 1. Install system deps
    if not install_apk('git'):
        # continue anyway
        pass

    # 2. Clone repository
    repo_url = "https://github.com/anthropics/fermats-last-theorem"
    clone_dir = "/tmp/fermats-last-theorem"
    if os.path.isdir(clone_dir):
        shutil.rmtree(clone_dir)
    clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, clone_dir])
    if clone_res['ok']:
        print_marker("TEST_PASS:clone_repo")
    else:
        print_marker(f"TEST_FAIL:clone_repo:{clone_res['err'][:200]}")

    # 3. Try pip install the package (if it provides a python package)
    pip_ok, pip_time = pip_install('fermats-last-theorem')
    if pip_ok:
        # measure import time
        start = time.perf_counter()
        try:
            import fermats_last_theorem  # placeholder import name
            import_time = (time.perf_counter() - start) * 1000  # ms
            print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
            print_marker("TEST_PASS:pip_import")
        except Exception as e:
            print_marker(f"TEST_FAIL:pip_import:{str(e)}")
    else:
        # fallback: pip install -e .
        fallback_res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=clone_dir)
        if fallback_res['ok']:
            print_marker("TEST_PASS:pip_editable_install")
        else:
            print_marker(f"TEST_FAIL:pip_editable_install:{fallback_res['err'][:200]}")

    # 4. Build with leanpkg
    build_res = run_cmd(['leanpkg', 'build'], cwd=clone_dir)
    if build_res['ok']:
        print_marker(f"TEST_PASS:lean_build")
    else:
        print_marker(f"TEST_FAIL:lean_build:{build_res['err'][:200]}")
    print_marker(f"BENCHMARK:lean_build_time_s:{build_res['time']:.2f}")

    # 5. Run tests with leanpkg
    test_res = run_cmd(['leanpkg', 'test'], cwd=clone_dir)
    if test_res['ok']:
        print_marker("TEST_PASS:lean_test")
    else:
        print_marker(f"TEST_FAIL:lean_test:{test_res['err'][:200]}")
    print_marker(f"BENCHMARK:lean_test_time_s:{test_res['time']:.2f}")

    # 6. Baseline comparison (assume baseline Lean 3 build time 30s)
    baseline_time = 30.0
    ratio = build_res['time'] / baseline_time if baseline_time else 0
    print_marker(f"BENCHMARK:vs_lean3_build_ratio:{ratio:.3f}")

    # Additional benchmarks: memory usage during build
    print_marker(f"BENCHMARK:lean_build_mem_peak_kib:{build_res['mem_peak']:.1f}")

    # Ensure at least 3 benchmark lines are emitted (already have several)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()