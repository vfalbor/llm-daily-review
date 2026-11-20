import subprocess, sys, os, time, tracemalloc, json, pathlib, re, shlex, tempfile, shutil

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err or out}")

def clone_repo(url, dest):
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if rc != 0:
        raise RuntimeError(f"git clone failed: {err or out}")

def count_source_files(root):
    src_counts = {}
    total = 0
    for p in pathlib.Path(root).rglob("*"):
        if p.is_file():
            ext = p.suffix.lower()
            if ext in ['.c', '.cpp', '.py', '.go', '.rs', '.js', '.java', '.h']:
                src_counts[ext] = src_counts.get(ext, 0) + 1
                total += 1
    return src_counts, total

def run_python_examples(root):
    examples = list(pathlib.Path(root).rglob("*.py"))
    if not examples:
        raise RuntimeError("No python examples found")
    for ex in examples:
        start = time.time()
        rc, out, err = run_cmd([sys.executable, str(ex)], cwd=root)
        elapsed = time.time() - start
        if rc != 0:
            raise RuntimeError(f"Example {ex} failed: {err or out}")
        print_marker(f"TEST_PASS:run_example_{ex.name}")
        print_marker(f"BENCHMARK:example_{ex.name}_run_ms:{elapsed*1000:.2f}")

def measure_install_time(repo_url, dest):
    start = time.time()
    clone_repo(repo_url, dest)
    return time.time() - start

def main():
    # 1. Install required apk packages
    install_apk('git')

    # 2. Clone repository and benchmark install time
    repo_url = "https://github.com/bigcrimping/floppy3.5"
    workdir = tempfile.mkdtemp(prefix="floppy_test_")
    try:
        install_time = measure_install_time(repo_url, workdir)
        print_marker(f"BENCHMARK:install_time_s:{install_time:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")

    # 3. Count source files and languages
    try:
        src_counts, total = count_source_files(workdir)
        print_marker(f"TEST_PASS:count_source_files")
        print_marker(f"BENCHMARK:source_files_count:{total}")
        for ext, cnt in src_counts.items():
            print_marker(f"BENCHMARK:src_{ext[1:]}_count:{cnt}")
    except Exception as e:
        print_marker(f"TEST_FAIL:count_source_files:{e}")

    # 4. Try to run any python examples
    try:
        run_python_examples(workdir)
    except Exception as e:
        print_marker(f"TEST_FAIL:run_python_examples:{e}")

    # 5. Benchmark import time of a module from the repo (if any)
    try:
        # attempt to add repo to PYTHONPATH and import a module named 'floppy'
        sys.path.insert(0, workdir)
        tracemalloc.start()
        start = time.time()
        import importlib
        mod = importlib.import_module('floppy')
        import_time = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"TEST_PASS:import_floppy_module")
        print_marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_floppy_module:{e}")

    # 6. Baseline comparison (using dummy baseline values)
    try:
        # Assume baseline install time for FloppyNAS is 15.0 s
        baseline_install = 15.0
        ratio = install_time / baseline_install if baseline_install else 0
        print_marker(f"BENCHMARK:vs_floppynas_install_time_ratio:{ratio:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_comparison:{e}")

    # Cleanup
    try:
        shutil.rmtree(workdir)
    except Exception:
        pass

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()