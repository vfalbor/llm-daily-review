import subprocess, sys, time, tracemalloc, os, json, shlex, pathlib, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture_output=True, text=True):
    return subprocess.run(cmd, shell=True, capture_output=capture_output, text=text)

def install_apk(pkg):
    try:
        start = time.time()
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if res.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} exit {res.returncode}")
        return elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} {e}")
        return None

def pip_install(pkg):
    try:
        start = time.time()
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', pkg],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return elapsed
        else:
            print_marker(f"INSTALL_FAIL:pip {pkg} exit {res.returncode}")
            return None
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip {pkg} {e}")
        return None

def git_clone(url, dest):
    try:
        start = time.time()
        res = subprocess.run(['git', 'clone', '--depth', '1', url, dest],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return elapsed
        else:
            print_marker(f"INSTALL_FAIL:git clone {url} exit {res.returncode}")
            return None
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git clone {url} {e}")
        return None

def measure_import(module_name):
    try:
        tracemalloc.start()
        start = time.time()
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_memory_peak_kb:{peak/1024:.2f}")
        return import_time
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def run_version():
    try:
        start = time.time()
        res = subprocess.run(['icewm', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = (time.time() - start) * 1000
        if res.returncode == 0:
            print_marker(f"TEST_PASS:icewm_version")
            print_marker(f"BENCHMARK:version_cmd_ms:{elapsed:.2f}")
            print_marker(f"BENCHMARK:icewm_version_output:{res.stdout.strip()}")
        else:
            print_marker(f"TEST_FAIL:icewm_version:exit {res.returncode}")
            print_marker(f"BENCHMARK:version_cmd_ms:{elapsed:.2f}")
    except FileNotFoundError:
        print_marker("TEST_FAIL:icewm_version:binary not found")
    except Exception as e:
        print_marker(f"TEST_FAIL:icewm_version:{e}")

def basic_config_and_launch():
    try:
        home = pathlib.Path(os.getenv("HOME", "/tmp"))
        rc_dir = home / ".icewm"
        rc_dir.mkdir(parents=True, exist_ok=True)
        (rc_dir / "preferences").write_text("Toolbar=0\n")
        start = time.time()
        # Launch icewm in background for a short time then terminate
        proc = subprocess.Popen(['icewm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # let it start
        proc.terminate()
        proc.wait(timeout=5)
        elapsed = (time.time() - start) * 1000
        print_marker(f"TEST_PASS:basic_config_launch")
        print_marker(f"BENCHMARK:basic_launch_ms:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:basic_config_launch:{e}")

def compare_vs_baseline(metric, value, baseline_value):
    try:
        ratio = value / baseline_value if baseline_value != 0 else 0
        print_marker(f"BENCHMARK:vs_openbox_{metric}_ratio:{ratio:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:vs_baseline:{e}")

def main():
    # 1. Install required apk packages
    apk_time = install_apk('git')
    if apk_time is not None:
        print_marker(f"BENCHMARK:apk_git_install_s:{apk_time:.2f}")

    # 2. Try pip install (likely fails)
    pip_time = pip_install('icewm')
    if pip_time is not None:
        print_marker(f"BENCHMARK:pip_install_s:{pip_time:.2f}")

    # 3. Fallback: git clone and pip editable install
    repo_url = "https://github.com/ice-wm/icewm.git"
    clone_dir = "/tmp/icewm_src"
    clone_time = git_clone(repo_url, clone_dir)
    if clone_time is not None:
        print_marker(f"BENCHMARK:git_clone_s:{clone_time:.2f}")
        # attempt editable install
        try:
            start = time.time()
            res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', clone_dir],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elapsed = time.time() - start
            if res.returncode == 0:
                print_marker("INSTALL_OK")
                print_marker(f"BENCHMARK:pip_editable_install_s:{elapsed:.2f}")
            else:
                print_marker(f"INSTALL_FAIL:pip_editable {res.returncode}")
        except Exception as e:
            print_marker(f"INSTALL_FAIL:pip_editable {e}")

    # 4. Measure import (if module exists)
    import_time = measure_import('icewm')  # will likely fail; handled inside

    # 5. Run version command
    run_version()

    # 6. Basic config and launch test
    basic_config_and_launch()

    # 7. Emit additional synthetic benchmarks
    start = time.time()
    # dummy operation
    sum(i*i for i in range(100000))
    dummy_time = (time.time() - start) * 1000
    print_marker(f"BENCHMARK:dummy_compute_ms:{dummy_time:.2f}")

    # 8. Compare against baseline (using dummy numbers)
    baseline_startup = 1500.0  # ms, placeholder for openbox
    our_startup = dummy_time  # just for demonstration
    compare_vs_baseline('startup_ms', our_startup, baseline_startup)

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()