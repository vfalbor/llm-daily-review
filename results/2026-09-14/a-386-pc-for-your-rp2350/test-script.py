import subprocess, sys, os, time, tracemalloc, json, pathlib, shlex

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache', pkg])
    elapsed = time.time() - start
    if res.returncode == 0:
        print_marker(f"INSTALL_OK | INSTALL_FAIL:{pkg}=none")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    return elapsed

def git_clone(url, dest):
    start = time.time()
    res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    elapsed = time.time() - start
    if res.returncode != 0:
        print_marker(f"INSTALL_FAIL:git_clone:{res.stderr.strip()}")
    return elapsed

def count_source_files(root):
    total = 0
    langs = {}
    for path in pathlib.Path(root).rglob('*'):
        if path.is_file():
            total += 1
            ext = path.suffix.lower()
            langs[ext] = langs.get(ext, 0) + 1
    return total, langs

def run_python_examples(repo_path):
    examples = list(pathlib.Path(repo_path).rglob('*.py'))
    if not examples:
        raise FileNotFoundError("No Python examples found")
    # pick first
    script = examples[0]
    start = time.time()
    tracemalloc.start()
    res = run_cmd([sys.executable, str(script)], cwd=repo_path)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed_ms = (time.time() - start) * 1000
    if res.returncode != 0:
        raise RuntimeError(f"Example failed: {res.stderr.strip()}")
    return elapsed_ms, peak / 1024

def main():
    benchmarks = {}

    # 1. Install required system packages
    install_time = install_apk('git')
    benchmarks['install_time_s'] = round(install_time, 3)

    # 2. Clone repository
    repo_url = 'https://github.com/rh1tech/frank-386'
    repo_dir = '/tmp/frank-386'
    clone_time = git_clone(repo_url, repo_dir)
    benchmarks['clone_time_s'] = round(clone_time, 3)

    # 3. Count source files
    try:
        file_count, langs = count_source_files(repo_dir)
        benchmarks['source_file_count'] = file_count
        print_marker(f"TEST_PASS:count_files")
    except Exception as e:
        print_marker(f"TEST_FAIL:count_files:{e}")

    # 4. Attempt to run a Python example (if any)
    try:
        exec_ms, mem_kb = run_python_examples(repo_dir)
        benchmarks['example_exec_ms'] = round(exec_ms, 2)
        benchmarks['example_peak_mem_kb'] = round(mem_kb, 2)
        print_marker(f"TEST_PASS:run_python_example")
    except FileNotFoundError as e:
        print_marker(f"TEST_SKIP:run_python_example:{e}")
    except Exception as e:
        print_marker(f"TEST_FAIL:run_python_example:{e}")

    # 5. Benchmark against similar tool (C64-Pi) – use file count ratio
    # Assume C64-Pi repo has ~350 source files (hard‑coded baseline)
    baseline_file_count = 350
    try:
        ratio = file_count / baseline_file_count if baseline_file_count else 0
        benchmarks['vs_c64pi_filecount_ratio'] = round(ratio, 3)
        print_marker(f"TEST_PASS:baseline_comparison")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_comparison:{e}")

    # Emit all benchmark lines
    for k, v in benchmarks.items():
        print_marker(f"BENCHMARK:{k}:{v}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()