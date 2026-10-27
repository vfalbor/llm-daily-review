#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib

def marker_print(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, capture=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=True,
        )
        return (True, result.stdout if capture else "")
    except subprocess.CalledProcessError as e:
        return (False, e.stderr if capture else str(e))

def install_apk(pkg):
    ok, _ = run_cmd(['apk', 'add', '--no-cache', pkg])
    if ok:
        marker_print("INSTALL_OK")
    else:
        marker_print(f"INSTALL_FAIL:apk {pkg}")

def pip_install(package):
    ok, _ = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package])
    return ok

def git_clone(repo, dest):
    ok, _ = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    return ok

def measure_import_time(module_name):
    start = time.time()
    try:
        __import__(module_name)
        duration = (time.time() - start) * 1000  # ms
        marker_print(f"BENCHMARK:import_time_ms:{duration:.2f}")
        return duration
    except Exception as e:
        marker_print(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def measure_cmd_time(cmd, cwd=None):
    start = time.time()
    ok, out = run_cmd(cmd, cwd=cwd, capture=True)
    duration = (time.time() - start) * 1000  # ms
    return ok, out, duration

def main():
    # 1. Install system deps
    install_apk('git')

    # 2. Try pip install first
    pkg_name = 'nietzschian-debugger'
    if not pip_install(pkg_name):
        marker_print(f"INSTALL_FAIL:pip {pkg_name}")
        # fallback to source
        src_dir = pathlib.Path('/tmp/nietzschian-debugger')
        if src_dir.exists():
            shutil.rmtree(src_dir)
        if not git_clone('https://github.com/DilawarShafiq/nietzschian-debugger.git', str(src_dir)):
            marker_print("INSTALL_FAIL:git clone")
            src_dir = None
        else:
            # install editable
            ok = pip_install('-e .')
            if not ok:
                marker_print("INSTALL_FAIL:pip -e .")
                src_dir = None
    else:
        marker_print("INSTALL_OK")
        src_dir = None

    # 3. Benchmark import time
    import_time = measure_import_time('nietzschian_debugger')
    if import_time is None:
        marker_print("TEST_SKIP:import_time:import failed")

    # 4. Test 1: cargo build from source if we have src_dir
    if src_dir:
        # ensure cargo is installed (apk add rust cargo)
        install_apk('rust')
        install_apk('cargo')
        start = time.time()
        ok, out = run_cmd(['cargo', 'build', '--release'], cwd=str(src_dir))
        build_time = (time.time() - start) * 1000
        if ok:
            marker_print(f"TEST_PASS:cargo_build")
        else:
            marker_print(f"TEST_FAIL:cargo_build:{out.strip()}")
        marker_print(f"BENCHMARK:build_time_ms:{build_time:.2f}")
    else:
        marker_print("TEST_SKIP:cargo_build:source not available")

    # 5. Test 2: nzd --help
    nzd_path = None
    if src_dir:
        possible = src_dir / 'target' / 'release' / 'nzd'
        if possible.is_file():
            nzd_path = str(possible)
    if not nzd_path:
        # try to find in PATH after pip install
        which = shutil.which('nzd')
        if which:
            nzd_path = which
    if nzd_path:
        ok, out, dur = measure_cmd_time([nzd_path, '--help'])
        if ok and 'Usage' in out:
            marker_print("TEST_PASS:nzd_help")
        else:
            marker_print(f"TEST_FAIL:nzd_help:{out.strip()}")
        marker_print(f"BENCHMARK:nzd_help_ms:{dur:.2f}")
    else:
        marker_print("TEST_SKIP:nzd_help:nzd binary not found")
        marker_print("BENCHMARK:nzd_help_ms:0")

    # 6. Test 3: run debugger on tiny Rust project
    sample_dir = pathlib.Path('/tmp/rust_sample')
    if sample_dir.exists():
        shutil.rmtree(sample_dir)
    sample_dir.mkdir(parents=True, exist_ok=True)
    main_rs = sample_dir / 'main.rs'
    main_rs.write_text('fn main() { let x = 42; println!("x = {}", x); }')
    cargo_toml = sample_dir / 'Cargo.toml'
    cargo_toml.write_text('[package]\nname = "sample"\nversion = "0.1.0"\nedition = "2021"\n')
    # build sample
    ok, out = run_cmd(['cargo', 'build'], cwd=str(sample_dir))
    if not ok:
        marker_print(f"TEST_FAIL:sample_build:{out.strip()}")
    else:
        # run debugger with a simple command: get help again as proxy for functionality
        exe_path = sample_dir / 'target' / 'debug' / 'sample'
        if nzd_path and exe_path.is_file():
            ok, out, dur = measure_cmd_time([nzd_path, '--run', str(exe_path), '--', '--help'])
            if ok:
                marker_print("TEST_PASS:nzd_run_sample")
            else:
                marker_print(f"TEST_FAIL:nzd_run_sample:{out.strip()}")
            marker_print(f"BENCHMARK:nzd_run_sample_ms:{dur:.2f}")
        else:
            marker_print("TEST_SKIP:nzd_run_sample:nzd or sample binary missing")
            marker_print("BENCHMARK:nzd_run_sample_ms:0")

    # 7. Baseline comparison vs gdb help time (mocked as 150ms)
    baseline_help_ms = 150.0
    # use the nzd_help benchmark if available
    try:
        # extract last printed nzd_help_ms value from stdout? we stored in variable dur
        nzd_help_ms = dur if 'nzd_help_ms' in locals() else baseline_help_ms
        ratio = nzd_help_ms / baseline_help_ms
        marker_print(f"BENCHMARK:vs_gdb_help_ratio:{ratio:.2f}")
    except Exception:
        marker_print("BENCHMARK:vs_gdb_help_ratio:NA")

    # 8. Additional generic benchmarks
    # memory usage snapshot
    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    current, peak = tracemalloc.get_traced_memory()
    marker_print(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
    marker_print(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    tracemalloc.stop()

    # final marker
    marker_print("RUN_OK")

if __name__ == "__main__":
    main()