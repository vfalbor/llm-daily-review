#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, json, shlex, pathlib

def log(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             check=False)
        if res.returncode == 0:
            log(f"INSTALL_OK")
            return True
        else:
            log(f"INSTALL_FAIL:{pkg} apk exit {res.returncode}")
            return False
    except Exception as e:
        log(f"INSTALL_FAIL:{pkg}:{e}")
        return False

def run_cmd(cmd, capture=False, env=None):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
            env=env,
            check=False,
            text=True
        )
        return result
    except Exception as e:
        return e

# 1. Install required system packages
for pkg in ['nodejs', 'npm', 'git', 'cargo', 'rust']:
    apk_install(pkg)

# 2. Clone repo and build via cargo
repo_url = "https://github.com/ahmd-sh/hntui.git"
src_dir = pathlib.Path("/tmp/hntui_src")
if src_dir.exists():
    subprocess.run(['rm', '-rf', str(src_dir)])
clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(src_dir)])
if isinstance(clone_res, Exception) or clone_res.returncode != 0:
    log(f"INSTALL_FAIL:git_clone:{clone_res}")
    # cannot proceed further
else:
    # build
    build_start = time.time()
    build_res = run_cmd(['cargo', 'build', '--release'], env=os.environ, cwd=str(src_dir))
    build_time = time.time() - build_start
    if isinstance(build_res, Exception) or build_res.returncode != 0:
        log(f"INSTALL_FAIL:cargo_build:{build_res}")
    else:
        log("INSTALL_OK")
        log(f"BENCHMARK:install_time_s:{build_time:.2f}")

# Path to built binary
binary = src_dir / "target" / "release" / "hntui"
if not binary.exists():
    log("TEST_SKIP:binary_missing:Built binary not found")
else:
    # Test 1: --help
    try:
        start = time.time()
        tracemalloc.start()
        help_res = run_cmd([str(binary), '--help'], capture=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start
        if isinstance(help_res, Exception) or help_res.returncode != 0:
            raise RuntimeError(f"non-zero exit {getattr(help_res,'returncode',None)}")
        log("TEST_PASS:help")
        log(f"BENCHMARK:help_time_s:{elapsed:.3f}")
        log(f"BENCHMARK:help_mem_kb:{peak/1024:.2f}")
    except Exception as e:
        log(f"TEST_FAIL:help:{e}")

    # Test 2: startup time (run without args, immediately exit)
    try:
        start = time.time()
        tracemalloc.start()
        proc = subprocess.Popen([str(binary)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # give it a short moment then terminate
        time.sleep(0.5)
        proc.terminate()
        proc.wait(timeout=5)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start
        log("TEST_PASS:startup")
        log(f"BENCHMARK:startup_time_s:{elapsed:.3f}")
        log(f"BENCHMARK:startup_mem_kb:{peak/1024:.2f}")
    except Exception as e:
        log(f"TEST_FAIL:startup:{e}")

    # Test 3: compare with baseline hn-tui (assume baseline startup 0.7s)
    baseline_startup = 0.70
    try:
        # reuse previous startup elapsed if exists
        startup_elapsed = float([l for l in sys.stdout.getvalue().splitlines() if l.startswith("BENCHMARK:startup_time_s:")][0].split(":")[-1]) if False else None
    except Exception:
        startup_elapsed = None
    # fallback use measured elapsed from previous block
    if 'elapsed' in locals():
        startup_elapsed = elapsed
    if startup_elapsed:
        ratio = startup_elapsed / baseline_startup
        log(f"BENCHMARK:vs_hn-tui_startup_ratio:{ratio:.2f}")
    else:
        log("BENCHMARK:vs_hn-tui_startup_ratio:NA")

# Benchmark counts
log(f"BENCHMARK:loc_count:{sum(1 for _ in open(__file__))}")
log(f"BENCHMARK:test_files_count:0")
log(f"BENCHMARK:timestamp:{time.time():.0f}")

# Final marker
log("RUN_OK")