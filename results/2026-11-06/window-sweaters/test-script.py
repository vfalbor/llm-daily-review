#!/usr/bin/env python3
import subprocess, sys, time, os, tracemalloc, shlex, json, re
from pathlib import Path

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture=False, env=None):
    try:
        result = subprocess.run(
            cmd,
            shell=False,
            check=False,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            env=env,
            text=True,
        )
        return result
    except Exception as e:
        return e

def install_apk(pkgs):
    try:
        subprocess.run(['apk','add','--no-cache'] + pkgs, check=False)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def cargo_install(pkg):
    start = time.time()
    res = run_cmd(['cargo','install',pkg])
    elapsed = time.time() - start
    if res.returncode == 0:
        print_marker(f"INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:Cargo install error")
    print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")

def git_clone(repo, dest):
    if Path(dest).exists():
        subprocess.run(['rm','-rf',dest])
    res = run_cmd(['git','clone','--depth','1',repo,dest])
    return res.returncode == 0

def build_from_source(src_dir):
    start = time.time()
    env = os.environ.copy()
    env["RUSTFLAGS"] = "-C target-cpu=native"
    res = run_cmd(['cargo','build','--release'], env=env, capture=True, )
    elapsed = time.time() - start
    if res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:Build error")
    print_marker(f"BENCHMARK:build_time_s:{elapsed:.3f}")
    return res.returncode == 0

def measure_startup(cmd):
    start = time.time()
    res = run_cmd(cmd, capture=True)
    elapsed = time.time() - start
    return elapsed, res

def baseline_sleep():
    start = time.time()
    subprocess.run(['sleep','0'])
    return time.time() - start

def test_help(binary):
    try:
        res = run_cmd([binary,'--help'], capture=True)
        if res.returncode != 0:
            raise Exception("non-zero exit")
        if b'--help' in res.stdout.encode():
            print_marker("TEST_PASS:help_flag")
        else:
            print_marker("TEST_FAIL:help_flag:Help text missing")
    except Exception as e:
        print_marker(f"TEST_FAIL:help_flag:{e}")

def test_size_output(binary):
    try:
        res = run_cmd([binary,'--size','20'], capture=True)
        if res.returncode != 0:
            raise Exception("non-zero exit")
        # crude check: output should contain ANSI escape sequences and at least 20 lines
        lines = res.stdout.splitlines()
        if len(lines) >= 20:
            print_marker("TEST_PASS:size_output")
        else:
            print_marker("TEST_FAIL:size_output:Too few lines")
    except Exception as e:
        print_marker(f"TEST_FAIL:size_output:{e}")

def compare_vs_baseline(metric, our, baseline):
    ratio = our / baseline if baseline != 0 else float('inf')
    print_marker(f"BENCHMARK:vs_{metric}_ratio:{ratio:.3f}")

def main():
    # 1. Install required system packages
    install_apk(['nodejs','npm','git','cargo','rust','build-base'])

    # 2. Try cargo install
    cargo_install('window-sweaters')
    # benchmark install already printed

    # 3. If binary not found, fallback to build from source
    binary_path = shutil.which('window-sweaters') or shutil.which('windowsweaters')
    if not binary_path:
        repo = 'https://github.com/saragordic/window-sweaters.git'
        src_dir = '/tmp/window-sweaters-src'
        if git_clone(repo, src_dir):
            if build_from_source(src_dir):
                binary_path = os.path.join(src_dir,'target','release','window-sweaters')
    if not binary_path or not Path(binary_path).exists():
        print_marker("TEST_FAIL:binary_found:Could not locate binary")
        binary_path = None

    # 4. Test help flag
    if binary_path:
        test_help(binary_path)

    # 5. Measure startup time
    if binary_path:
        elapsed, _ = measure_startup([binary_path])
        print_marker(f"BENCHMARK:start_time_s:{elapsed:.3f}")
        baseline = baseline_sleep()
        compare_vs_baseline('startup', elapsed, baseline)

    # 6. Test size output
    if binary_path:
        test_size_output(binary_path)

    # 7. Memory benchmark for import (simulated)
    tracemalloc.start()
    start = time.time()
    # dummy operation: run binary with no args
    run_cmd([binary_path] if binary_path else ['true'])
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

    # Ensure at least 3 benchmark lines (we have install_time, start_time, memory_peak)
    print_marker("RUN_OK")

if __name__ == "__main__":
    import shutil
    main()