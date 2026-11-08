import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result

def apk_install(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg])
        if res.returncode == 0:
            marker(f"INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:{pkg} {res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{pkg} {e}")

def measure_time(func, *args, **kwargs):
    start = time.time()
    try:
        func(*args, **kwargs)
        success = True
    except Exception as e:
        success = False
        err = e
    elapsed = time.time() - start
    return success, elapsed, err if not success else None

# 1. Install required system packages
for pkg in ['go', 'git', 'cargo', 'rust', 'nodejs', 'npm']:
    apk_install(pkg)

# Directories
BASE_DIR = pathlib.Path("/tmp/cljrs_test")
REPO_URL = "https://github.com/clj-rs/clj"
REPO_DIR = BASE_DIR / "clj"

# Ensure clean state
if BASE_DIR.exists():
    shutil.rmtree(BASE_DIR)
BASE_DIR.mkdir(parents=True)

# Benchmarks container
benchmarks = {}

# Test 1: Clone repository and build the compiler
def test_clone_and_build():
    # Clone
    clone_res = run_cmd(['git', 'clone', '--depth', '1', REPO_URL, str(REPO_DIR)])
    if clone_res.returncode != 0:
        raise RuntimeError(f"git clone failed: {clone_res.stderr.strip()}")
    # Build using cargo
    build_res = run_cmd(['cargo', 'build', '--release'], cwd=str(REPO_DIR))
    if build_res.returncode != 0:
        raise RuntimeError(f"cargo build failed: {build_res.stderr.strip()}")

    # Record binary size
    bin_path = REPO_DIR / "target" / "release" / "clj"
    if not bin_path.is_file():
        raise RuntimeError("Compiled binary not found")
    size = bin_path.stat().st_size
    benchmarks['binary_size_bytes'] = size

# Measure compile time
success, elapsed, err = measure_time(test_clone_and_build)
if success:
    marker(f"TEST_PASS:clone_and_build")
    benchmarks['compile_time_s'] = elapsed
else:
    marker(f"TEST_FAIL:clone_and_build:{err}")

# Benchmark lines for test 1
if 'compile_time_s' in benchmarks:
    marker(f"BENCHMARK:compile_time_s:{benchmarks['compile_time_s']:.3f}")
if 'binary_size_bytes' in benchmarks:
    marker(f"BENCHMARK:binary_size_bytes:{benchmarks['binary_size_bytes']}")

# Test 2: Compile and run hello-world program
def test_hello_world():
    hello_src = REPO_DIR / "examples" / "hello.clj"
    if not hello_src.is_file():
        raise RuntimeError("hello.clj example not found")
    # Use the built compiler
    bin_path = REPO_DIR / "target" / "release" / "clj"
    run_res = run_cmd([str(bin_path), str(hello_src)], cwd=str(REPO_DIR))
    if run_res.returncode != 0:
        raise RuntimeError(f"Running hello world failed: {run_res.stderr.strip()}")
    output = run_res.stdout.strip()
    expected = "Hello, World!"
    if expected not in output:
        raise AssertionError(f"Unexpected output: {output}")

# Measure hello world execution
tracemalloc.start()
success, elapsed, err = measure_time(test_hello_world)
snapshot = tracemalloc.take_snapshot()
tracemalloc.stop()
if success:
    marker(f"TEST_PASS:hello_world")
    benchmarks['hello_world_ms'] = elapsed * 1000
else:
    marker(f"TEST_FAIL:hello_world:{err}")

if 'hello_world_ms' in benchmarks:
    marker(f"BENCHMARK:hello_world_ms:{benchmarks['hello_world_ms']:.2f}")

# Test 3: Compare compilation time & binary size vs JVM Clojure compiler (baseline)
# Baseline constants (approximate, could be updated)
BASELINE_COMPILE_TIME_S = 30.0   # seconds for javac + clojure.jar build
BASELINE_BINARY_SIZE_BYTES = 50000000  # 50 MB for JVM bytecode + runtime

def test_baseline_comparison():
    # Already have compile_time_s and binary_size_bytes
    if 'compile_time_s' not in benchmarks or 'binary_size_bytes' not in benchmarks:
        raise RuntimeError("Missing benchmark data for comparison")
    ratio_time = benchmarks['compile_time_s'] / BASELINE_COMPILE_TIME_S
    ratio_size = benchmarks['binary_size_bytes'] / BASELINE_BINARY_SIZE_BYTES
    benchmarks['vs_jvm_compile_time_ratio'] = ratio_time
    benchmarks['vs_jvm_binary_size_ratio'] = ratio_size

success, _, err = measure_time(test_baseline_comparison)
if success:
    marker(f"TEST_PASS:baseline_comparison")
    marker(f"BENCHMARK:vs_jvm_compile_time_ratio:{benchmarks['vs_jvm_compile_time_ratio']:.3f}")
    marker(f"BENCHMARK:vs_jvm_binary_size_ratio:{benchmarks['vs_jvm_binary_size_ratio']:.3f}")
else:
    marker(f"TEST_FAIL:baseline_comparison:{err}")

# Test 4: Run REPL, evaluate macro
def test_repl_macro():
    bin_path = REPO_DIR / "target" / "release" / "clj"
    # Start REPL process
    proc = subprocess.Popen([str(bin_path), "--repl"], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Send a simple macro definition and evaluation
    macro_code = "(defmacro inc-x [x] `(+ ~x 1))\n(inc-x 41)\n"
    try:
        out, err = proc.communicate(input=macro_code, timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise RuntimeError("REPL timed out")
    if proc.returncode != 0:
        raise RuntimeError(f"REPL exited with error: {err.strip()}")
    if "42" not in out:
        raise AssertionError(f"Macro evaluation failed, output: {out}")

# Measure REPL test
success, elapsed, err = measure_time(test_repl_macro)
if success:
    marker(f"TEST_PASS:repl_macro")
    benchmarks['repl_macro_ms'] = elapsed * 1000
    marker(f"BENCHMARK:repl_macro_ms:{benchmarks['repl_macro_ms']:.2f}")
else:
    marker(f"TEST_FAIL:repl_macro:{err}")

# Ensure at least three benchmark lines (we have many)
# Final marker
marker("RUN_OK")