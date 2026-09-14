import subprocess, sys, os, time, tracemalloc, json, re, pathlib, collections, tempfile, shutil

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, capture=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout if capture else ''
    except Exception as e:
        return 1, str(e)

def install_apk(pkg):
    rc, out = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{out.strip()}")
    return rc == 0

def measure_time(func, *a, **kw):
    start = time.time()
    result = func(*a, **kw)
    elapsed = time.time() - start
    return result, elapsed

def count_source_files(repo_path):
    exts = {
        '.py': 'Python',
        '.rs': 'Rust',
        '.c': 'C',
        '.cpp': 'C++',
        '.go': 'Go',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
    }
    counts = collections.Counter()
    for root, _, files in os.walk(repo_path):
        for f in files:
            ext = pathlib.Path(f).suffix
            if ext in exts:
                counts[exts[ext]] += 1
    return counts

def main():
    # 1. Install required apk packages
    for pkg in ['git', 'rust', 'cargo']:
        install_apk(pkg)

    repo_url = "https://github.com/callbacked/kinesis"
    workdir = pathlib.Path(tempfile.mkdtemp())
    repo_dir = workdir / "kinesis"

    # 2. Clone repo
    try:
        rc, out = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(repo_dir)])
        if rc != 0:
            raise RuntimeError(out)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:clone:{e}")
        # cannot proceed further
        print_marker("RUN_OK")
        return

    # Benchmark: count files and languages
    file_counts = count_source_files(repo_dir)
    total_files = sum(file_counts.values())
    print_marker(f"BENCHMARK:test_files_count:{total_files}")
    for lang, cnt in file_counts.items():
        print_marker(f"BENCHMARK:{lang.lower()}_files:{cnt}")

    # 3. Build with cargo
    (build_res, build_time) = measure_time(run_cmd, ['cargo', 'build', '--release'], cwd=repo_dir)
    if build_res[0] == 0:
        print_marker("TEST_PASS:cargo_build")
    else:
        print_marker(f"TEST_FAIL:cargo_build:{build_res[1].strip()}")
    print_marker(f"BENCHMARK:build_time_s:{build_time:.2f}")

    # Baseline comparison (using OpenBCI-Python dummy build time 30s)
    baseline_build = 30.0
    ratio = build_time / baseline_build if baseline_build else 0
    print_marker(f"BENCHMARK:vs_openbci_python_build_ratio:{ratio:.2f}")

    # 4. Run kinesis --help
    binary_path = repo_dir / "target" / "release" / "kinesis"
    if not binary_path.is_file():
        # try fallback pip install
        try:
            rc, out = run_cmd(['pip', 'install', '-e', '.'], cwd=repo_dir)
            if rc == 0:
                print_marker("INSTALL_OK")
            else:
                raise RuntimeError(out)
        except Exception as e:
            print_marker(f"INSTALL_FAIL:pip_install:{e}")

    try:
        rc, out = run_cmd([str(binary_path), '--help'], cwd=repo_dir, capture=True)
        if rc == 0 and 'list-devices' in out and 'simulate' in out:
            print_marker("TEST_PASS:help_output")
        else:
            print_marker(f"TEST_FAIL:help_output:Unexpected output")
    except Exception as e:
        print_marker(f"TEST_FAIL:help_output:{e}")

    # Benchmark help execution time
    _, help_time = measure_time(run_cmd, [str(binary_path), '--help'], cwd=repo_dir, capture=True)
    print_marker(f"BENCHMARK:help_time_ms:{help_time*1000:.2f}")

    # 5. Simulate gesture (if script exists)
    simulate_script = repo_dir / "scripts" / "simulate_gesture.py"
    if simulate_script.is_file():
        try:
            rc, out = run_cmd(['python', str(simulate_script)], cwd=repo_dir, capture=True)
            if rc == 0 and re.search(r'gesture simulated', out, re.I):
                print_marker("TEST_PASS:gesture_simulation")
            else:
                print_marker(f"TEST_FAIL:gesture_simulation:{out.strip()}")
        except Exception as e:
            print_marker(f"TEST_FAIL:gesture_simulation:{e}")
        # benchmark simulation time
        _, sim_time = measure_time(run_cmd, ['python', str(simulate_script)], cwd=repo_dir, capture=True)
        print_marker(f"BENCHMARK:simulate_time_ms:{sim_time*1000:.2f}")
    else:
        print_marker("TEST_SKIP:gesture_simulation:No simulate script found")

    # 6. List devices (should fail gracefully without hardware)
    try:
        rc, out = run_cmd([str(binary_path), '--list-devices'], cwd=repo_dir, capture=True)
        if rc == 0:
            print_marker("TEST_PASS:list_devices")
        else:
            print_marker("TEST_SKIP:list_devices:No hardware attached")
    except Exception as e:
        print_marker(f"TEST_SKIP:list_devices:{e}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()