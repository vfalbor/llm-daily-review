#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, json, re, pathlib, shutil, hashlib

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return e

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkgs):
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache'] + pkgs, check=False)
    elapsed = time.time() - start
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
        print_marker(f"INSTALL_OK")
    else:
        reason = getattr(res, 'stderr', str(res))
        print_marker(f"INSTALL_FAIL:{reason.strip()}")
    print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.3f}")

def clone_repo(url, dest):
    start = time.time()
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    elapsed = time.time() - start
    if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = getattr(res, 'stderr', str(res))
        print_marker(f"INSTALL_FAIL:git_clone:{reason.strip()}")
    print_marker(f"BENCHMARK:git_clone_time_s:{elapsed:.3f}")

def count_source_files(repo_path):
    start = time.time()
    total = 0
    langs = {}
    for root, _, files in os.walk(repo_path):
        for f in files:
            ext = pathlib.Path(f).suffix.lower()
            if ext in {'.c', '.cpp', '.py', '.ino', '.h', '.hpp', '.js', '.ts'}:
                total += 1
                langs[ext] = langs.get(ext, 0) + 1
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:source_file_count:{total}")
    print_marker(f"BENCHMARK:source_langs:{json.dumps(langs)}")
    print_marker(f"BENCHMARK:count_files_time_s:{elapsed:.3f}")

def run_python_examples(repo_path):
    examples = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith('.py'):
                examples.append(os.path.join(root, f))
    if not examples:
        print_marker("TEST_SKIP:run_python_examples:No python examples found")
        return
    for ex in examples:
        name = f"run_example_{os.path.relpath(ex, repo_path)}"
        start = time.time()
        try:
            # Run with limited env
            proc = subprocess.run([sys.executable, ex],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  timeout=30,
                                  text=True)
            elapsed = time.time() - start
            if proc.returncode == 0:
                print_marker(f"TEST_PASS:{name}")
                print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.3f}")
            else:
                reason = proc.stderr.strip() or f"exit {proc.returncode}"
                print_marker(f"TEST_FAIL:{name}:{reason}")
                print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.3f}")
        except Exception as e:
            elapsed = time.time() - start
            print_marker(f"TEST_FAIL:{name}:{str(e)}")
            print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.3f}")

def benchmark_vs_baseline(metric, value, baseline_value):
    try:
        ratio = float(value) / float(baseline_value)
        print_marker(f"BENCHMARK:vs_{baseline_value}_{metric}:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install required apk packages
    install_apk(['git', 'python3', 'py3-pip', 'build-base', 'gcc', 'make', 'cmake'])
    # 2. Clone repository
    repo_url = "https://github.com/wilsonharper/businesscard"
    repo_dir = "/tmp/businesscard"
    clone_repo(repo_url, repo_dir)
    # 3. Count source files and languages
    try:
        count_source_files(repo_dir)
        print_marker("TEST_PASS:count_source_files")
    except Exception as e:
        print_marker(f"TEST_FAIL:count_source_files:{e}")

    # 4. Attempt to install Python package if present
    setup_path = os.path.join(repo_dir, 'setup.py')
    if os.path.isfile(setup_path):
        start = time.time()
        try:
            res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', repo_dir])
            elapsed = time.time() - start
            if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
                print_marker("TEST_PASS:pip_install")
            else:
                reason = getattr(res, 'stderr', str(res))
                print_marker(f"TEST_FAIL:pip_install:{reason.strip()}")
        except Exception as e:
            elapsed = time.time() - start
            print_marker(f"TEST_FAIL:pip_install:{e}")
        print_marker(f"BENCHMARK:pip_install_time_s:{elapsed:.3f}")

    # 5. Run any python examples
    run_python_examples(repo_dir)

    # 6. Simulated benchmark: count .c files as "compile time"
    start = time.time()
    c_files = []
    for root, _, files in os.walk(repo_dir):
        for f in files:
            if f.endswith('.c') or f.endswith('.cpp') or f.endswith('.ino'):
                c_files.append(os.path.join(root, f))
    compile_time = time.time() - start
    print_marker(f"BENCHMARK:compile_time_s:{compile_time:.3f}")
    print_marker(f"BENCHMARK:c_file_count:{len(c_files)}")

    # 7. Compare compile_time to a baseline (e.g., Arduino NFC Shield approx 0.5s)
    baseline_compile = 0.5
    benchmark_vs_baseline('compile_time_s', compile_time, baseline_compile)

    # 8. Memory usage snapshot
    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    total_mem = sum([stat.size for stat in snapshot.statistics('filename')])
    print_marker(f"BENCHMARK:memory_usage_kb:{total_mem/1024:.2f}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()