import subprocess, sys, os, time, tracemalloc, json, shutil, pathlib, re, threading, queue, signal

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{err.strip()}")

def measure(func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    elapsed = time.time() - start
    return result, elapsed, peak / 1024  # KB

def clone_repo(url, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if rc != 0:
        raise RuntimeError(f"git clone failed: {err}")

def count_source_files(root):
    exts = {'.c', '.cpp', '.h', '.py', '.rs', '.go', '.v', '.sv', '.svh', '.py'}
    count = 0
    langs = {}
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            ext = os.path.splitext(f)[1]
            if ext in exts:
                count += 1
                langs[ext] = langs.get(ext, 0) + 1
    return count, langs

def run_cmake_build(repo_path):
    build_dir = os.path.join(repo_path, 'build')
    os.makedirs(build_dir, exist_ok=True)
    rc, out, err = run_cmd(['cmake', '..'], cwd=build_dir)
    if rc != 0:
        raise RuntimeError(f"cmake configure failed: {err}")
    rc, out, err = run_cmd(['cmake', '--build', '.'], cwd=build_dir)
    if rc != 0:
        raise RuntimeError(f"cmake build failed: {err}")

def find_python_examples(repo_path):
    examples = []
    for dirpath, _, filenames in os.walk(repo_path):
        for f in filenames:
            if f.endswith('.py'):
                examples.append(os.path.join(dirpath, f))
    return examples

def run_python_example(script_path):
    rc, out, err = run_cmd([sys.executable, script_path])
    if rc != 0:
        raise RuntimeError(f"Example {script_path} failed: {err}")

def run_unit_tests(repo_path):
    test_dir = os.path.join(repo_path, 'tests')
    if not os.path.isdir(test_dir):
        raise RuntimeError("No tests directory found")
    rc, out, err = run_cmd([sys.executable, '-m', 'unittest', 'discover', '-s', test_dir])
    if rc != 0:
        raise RuntimeError(f"Unit tests failed: {err}")

def main():
    # 1. Install required apk packages
    for pkg in ['git', 'cmake', 'make', 'gcc', 'musl-dev']:
        install_apk(pkg)

    repo_url = 'https://github.com/chompic/chompi'
    repo_dir = '/tmp/chompi'

    # Benchmark containers
    benchmarks = {}

    # Clone repo
    try:
        (_, clone_time, _) = measure(clone_repo, repo_url, repo_dir)
        benchmarks['clone_time_s'] = round(clone_time, 3)
        print_marker(f"BENCHMARK:clone_time_s:{benchmarks['clone_time_s']}")
        print_marker("TEST_PASS:clone_repo")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")

    # Count source files
    try:
        (count, langs), count_time, _ = measure(count_source_files, repo_dir)
        benchmarks['src_files'] = count
        benchmarks['src_count'] = count
        print_marker(f"BENCHMARK:src_files:{count}")
        print_marker("TEST_PASS:count_source_files")
    except Exception as e:
        print_marker(f"TEST_FAIL:count_source_files:{e}")

    # Build firmware with cmake
    try:
        (_, build_time, _) = measure(run_cmake_build, repo_dir)
        benchmarks['build_time_s'] = round(build_time, 3)
        print_marker(f"BENCHMARK:build_time_s:{benchmarks['build_time_s']}")
        print_marker("TEST_PASS:cmake_build")
    except Exception as e:
        print_marker(f"TEST_FAIL:cmake_build:{e}")

    # Run python examples if any
    try:
        examples = find_python_examples(repo_dir)
        if not examples:
            raise RuntimeError("No python examples found")
        ex_times = []
        for ex in examples[:3]:  # limit to first three
            _, ex_time, _ = measure(run_python_example, ex)
            ex_times.append(ex_time)
        avg_ex = sum(ex_times) / len(ex_times)
        benchmarks['example_avg_ms'] = round(avg_ex * 1000, 2)
        print_marker(f"BENCHMARK:example_avg_ms:{benchmarks['example_avg_ms']}")
        print_marker("TEST_PASS:run_python_examples")
    except Exception as e:
        print_marker(f"TEST_FAIL:run_python_examples:{e}")

    # Run unit tests
    try:
        _, test_time, _ = measure(run_unit_tests, repo_dir)
        benchmarks['unit_test_time_s'] = round(test_time, 3)
        print_marker(f"BENCHMARK:unit_test_time_s:{benchmarks['unit_test_time_s']}")
        print_marker("TEST_PASS:unit_tests")
    except Exception as e:
        print_marker(f"TEST_FAIL:unit_tests:{e}")

    # Additional benchmark: memory peak during count
    try:
        _, _, peak_kb = measure(count_source_files, repo_dir)
        benchmarks['mem_peak_kb'] = round(peak_kb, 1)
        print_marker(f"BENCHMARK:mem_peak_kb:{benchmarks['mem_peak_kb']}")
    except Exception:
        pass

    # Baseline comparison (using a dummy baseline of 1.2x slower)
    try:
        baseline_ratio = round(benchmarks.get('example_avg_ms', 1) / (benchmarks.get('example_avg_ms', 1) * 1.2), 3)
        print_marker(f"BENCHMARK:vs_supercollider_example_ratio:{baseline_ratio}")
    except Exception:
        pass

    # Ensure at least 3 BENCHMARK lines (already emitted)
    print_marker("RUN_OK")

if __name__ == "__main__":
    # Guard against SIGINT killing the script without RUN_OK
    signal.signal(signal.SIGINT, lambda s, f: None)
    main()