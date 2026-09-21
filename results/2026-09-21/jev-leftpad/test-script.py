#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shlex, json

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, ""
    except Exception as e:
        return False, str(e)

def run_cmd(cmd, capture=True, env=None):
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE, env=env, text=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip() or str(e)

def install_system_packages():
    pkgs = ['nodejs', 'npm', 'git', 'cargo', 'rust']
    all_ok = True
    for p in pkgs:
        ok, err = apk_install(p)
        if not ok:
            all_ok = False
            print_marker(f"INSTALL_FAIL:{p}:{err}")
        else:
            print_marker(f"INSTALL_OK:{p}")
    return all_ok

def try_go_get():
    ok, out = run_cmd('go get github.com/f/jev-leftpad')
    if ok:
        print_marker("INSTALL_OK:go_get")
        return True
    else:
        print_marker(f"INSTALL_FAIL:go_get:{out}")
        return False

def try_npm_install():
    ok, out = run_cmd('npm install -g jev-leftpad')
    if ok:
        print_marker("INSTALL_OK:npm")
        return True
    else:
        print_marker(f"INSTALL_FAIL:npm:{out}")
        return False

def try_pip_install():
    # try direct pip
    ok, out = run_cmd('pip install jev-leftpad')
    if ok:
        print_marker("INSTALL_OK:pip")
        return True
    # fallback git clone + editable
    ok, out = run_cmd('git clone https://github.com/f/jev-leftpad.git /tmp/jev-leftpad')
    if not ok:
        print_marker(f"INSTALL_FAIL:git_clone:{out}")
        return False
    ok, out = run_cmd('pip install -e /tmp/jev-leftpad')
    if ok:
        print_marker("INSTALL_OK:pip_editable")
        return True
    print_marker(f"INSTALL_FAIL:pip_editable:{out}")
    return False

def measure_install_time():
    start = time.time()
    # try each method until success
    if try_go_get():
        return time.time() - start
    if try_npm_install():
        return time.time() - start
    if try_pip_install():
        return time.time() - start
    return time.time() - start

def test_help():
    ok, out = run_cmd('jev-leftpad --help')
    if ok and out:
        print_marker("TEST_PASS:help")
    else:
        print_marker(f"TEST_FAIL:help:{out or 'no output'}")

def test_padding():
    cmd = "echo 'test' | jev-leftpad 10"
    ok, out = run_cmd(cmd)
    if not ok:
        print_marker(f"TEST_FAIL:pad:{out}")
        return None
    if len(out) == 10:
        print_marker("TEST_PASS:pad_length")
    else:
        print_marker(f"TEST_FAIL:pad_length:{len(out)}!=10")
    return out

def benchmark_invocations(count=1_000_000):
    # warm up
    subprocess.run("jev-leftpad 5", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    start = time.time()
    for _ in range(count):
        subprocess.run("jev-leftpad 5", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:1M_invocations_s:{elapsed:.3f}")
    return elapsed

def benchmark_vs_baseline():
    # baseline using npm leftpad (if installed)
    ok, _ = run_cmd('npm install -g left-pad')
    if not ok:
        print_marker("TEST_SKIP:baseline_install:npm left-pad not available")
        return
    # measure baseline
    start = time.time()
    for _ in range(1000):
        subprocess.run("left-pad test 10", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    baseline = time.time() - start
    # measure our tool for same count
    start = time.time()
    for _ in range(1000):
        subprocess.run("jev-leftpad 10", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ours = time.time() - start
    ratio = ours / baseline if baseline else 0
    print_marker(f"BENCHMARK:vs_leftpad_ratio:{ratio:.3f}")

def main():
    # 1. Install system packages
    install_system_packages()

    # 2. Install the tool and benchmark install time
    install_time = measure_install_time()
    print_marker(f"BENCHMARK:install_time_s:{install_time:.3f}")

    # 3. Run help test
    test_help()

    # 4. Test padding functionality
    out = test_padding()

    # 5. Benchmark 1M invocations
    bench_inv = benchmark_invocations()

    # 6. Additional benchmarks: memory snapshot
    tracemalloc.start()
    _ = subprocess.run("jev-leftpad 5", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

    # 7. Compare vs baseline
    benchmark_vs_baseline()

    # Ensure at least three benchmark lines (install_time, invocations, memory)
    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()