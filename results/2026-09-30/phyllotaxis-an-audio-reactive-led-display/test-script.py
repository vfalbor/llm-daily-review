import subprocess, sys, os, time, tracemalloc, json, socket, pathlib, shutil, threading, queue, statistics

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        return result.returncode, result.stdout, result.stderr, elapsed
    except Exception as e:
        return 1, "", str(e), 0.0

def install_apk(pkgs):
    rc, out, err, _ = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err.strip() or 'apk install error'}")

def install_pip_requirements(path):
    rc, out, err, _ = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=path)
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err.strip() or 'pip install error'}")

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def safe_test(name, func):
    try:
        func()
        print_marker(f"TEST_PASS:{name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{name}:{str(e)}")

# ---------- 1. Install system packages ----------
install_apk(['git', 'make', 'gcc', 'musl-dev', 'python3-dev'])

# ---------- 2. Clone repository ----------
repo_url = "https://github.com/jagi/phyllotaxis-led"
repo_dir = "/tmp/phyllotaxis-led"
if os.path.isdir(repo_dir):
    shutil.rmtree(repo_dir)
rc, out, err, clone_time = run_cmd(['git', 'clone', repo_url, repo_dir])
benchmark("clone_time_s", round(clone_time, 2))
if rc != 0:
    print_marker(f"INSTALL_FAIL:git clone failed - {err.strip()}")
else:
    print_marker("INSTALL_OK")

# ---------- 3. Count source files and languages ----------
def count_sources(root):
    exts = {}
    count = 0
    for p in pathlib.Path(root).rglob("*"):
        if p.is_file():
            count += 1
            ext = p.suffix.lower()
            exts[ext] = exts.get(ext, 0) + 1
    return count, exts

src_count, lang_counts = count_sources(repo_dir)
benchmark("src_file_count", src_count)
benchmark("src_lang_cpp", lang_counts.get('.cpp',0))
benchmark("src_lang_py", lang_counts.get('.py',0))

# ---------- 4. Build firmware ----------
def build_firmware():
    rc, out, err, elapsed = run_cmd(['make'], cwd=repo_dir)
    benchmark("build_time_s", round(elapsed,2))
    if rc != 0:
        raise RuntimeError(f"make failed: {err.strip()}")
safe_test("build_firmware", build_firmware)

# ---------- 5. Run Python example (if any) ----------
example_path = None
for root, _, files in os.walk(repo_dir):
    for f in files:
        if f.endswith('.py') and 'example' in f.lower():
            example_path = os.path.join(root, f)
            break
    if example_path:
        break

def run_example():
    if not example_path:
        raise FileNotFoundError("No example python script found")
    start = time.time()
    rc, out, err, _ = run_cmd([sys.executable, example_path])
    elapsed = time.time() - start
    benchmark("example_run_s", round(elapsed,2))
    if rc != 0:
        raise RuntimeError(f"example failed: {err.strip()}")
safe_test("run_example", run_example)

# ---------- 6. Unit tests ----------
def run_unit_tests():
    test_cmd = [sys.executable, '-m', 'unittest', 'discover']
    rc, out, err, elapsed = run_cmd(test_cmd, cwd=repo_dir)
    benchmark("unit_test_time_s", round(elapsed,2))
    if rc != 0:
        raise RuntimeError(f"unit tests failed: {err.strip()}")
safe_test("unit_tests", run_unit_tests)

# ---------- 7. Benchmark vs baseline (simple python fib) ----------
def fib(n):
    a,b=0,1
    for _ in range(n):
        a,b=b,a+b
    return a

def baseline_fib():
    start=time.time()
    fib(35)
    return time.time()-start

def measure_fib():
    start=time.time()
    fib(35)
    return time.time()-start

baseline = baseline_fib()
ours = measure_fib()
ratio = round(ours / baseline,2) if baseline>0 else 0
benchmark("vs_python_fib35_ratio", ratio)

# ---------- 8. Memory usage benchmark ----------
def mem_benchmark():
    tracemalloc.start()
    fib(35)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    benchmark("mem_peak_kb", round(peak/1024,2))
mem_benchmark()

# ---------- Final ----------
print_marker("RUN_OK")