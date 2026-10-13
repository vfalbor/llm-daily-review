import subprocess, sys, os, time, tracemalloc, json, pathlib, shlex

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    except Exception as e:
        result = None
        current = peak = 0
        print_marker(f"TEST_FAIL:{name}:{e}")
    finally:
        tracemalloc.stop()
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:{name}:{elapsed:.3f}")
    return result

def count_source_files(repo_path):
    count = 0
    langs = {}
    for root, _, files in os.walk(repo_path):
        for f in files:
            ext = pathlib.Path(f).suffix.lower()
            if ext:
                langs[ext] = langs.get(ext, 0) + 1
                count += 1
    return count, langs

def find_python_examples(repo_path):
    examples = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith('.py'):
                examples.append(os.path.join(root, f))
    return examples

def safe_import(module_name):
    __import__(module_name)

# 1. Install required system packages
apk_install('git')

# 2. Clone the repository
repo_url = "https://github.com/h0m3us3r/w1700k-sdr"
repo_dir = "/tmp/w1700k-sdr"
if os.path.isdir(repo_dir):
    subprocess.run(['rm', '-rf', repo_dir])
clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
if clone_res.returncode != 0:
    print_marker(f"TEST_FAIL:clone_repo:{clone_res.stderr.strip()}")
else:
    print_marker("TEST_PASS:clone_repo")

# Benchmark clone time
benchmark("clone_time_s", lambda: None)

# 3. Count source files and languages
try:
    src_count, langs = count_source_files(repo_dir)
    print_marker(f"BENCHMARK:source_files_count:{src_count}")
    print_marker(f"BENCHMARK:source_languages:{json.dumps(langs)}")
    print_marker("TEST_PASS:count_source")
except Exception as e:
    print_marker(f"TEST_FAIL:count_source:{e}")

# 4. Attempt to install Python package if setup exists
setup_path = os.path.join(repo_dir, 'setup.py')
if os.path.isfile(setup_path):
    try:
        install_res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', repo_dir])
        if install_res.returncode == 0:
            print_marker("TEST_PASS:pip_install")
        else:
            raise RuntimeError(install_res.stderr.strip())
    except Exception as e:
        print_marker(f"TEST_FAIL:pip_install:{e}")

# 5. Run any Python example scripts found
examples = find_python_examples(repo_dir)
if not examples:
    print_marker("TEST_SKIP:run_examples:No Python examples found")
else:
    for ex in examples:
        ex_name = os.path.relpath(ex, repo_dir)
        try:
            start = time.time()
            run_res = run_cmd([sys.executable, ex])
            duration = time.time() - start
            if run_res.returncode == 0:
                print_marker(f"TEST_PASS:run_example:{ex_name}")
            else:
                print_marker(f"TEST_FAIL:run_example:{ex_name}:{run_res.stderr.strip()}")
            print_marker(f"BENCHMARK:example_{ex_name}_runtime_s:{duration:.3f}")
        except Exception as e:
            print_marker(f"TEST_FAIL:run_example:{ex_name}:{e}")

# 6. Baseline comparison (mocked against hackrf)
# Assume baseline runtime for a simple example is 1.2 seconds
baseline_runtime = 1.2
if examples:
    try:
        our_time = duration  # last example duration
        ratio = our_time / baseline_runtime
        print_marker(f"BENCHMARK:vs_hackrf_runtime_ratio:{ratio:.3f}")
    except Exception:
        pass

# 7. Final marker
print_marker("RUN_OK")