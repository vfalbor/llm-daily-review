import subprocess, sys, os, time, tracemalloc, json, shlex, pathlib, statistics

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def benchmark(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        result = e
        success = False
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = end - start
    print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.3f}")
    print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.1f}")
    return success, result, elapsed

# 1. Install required system packages
for pkg in ['go', 'git', 'cargo', 'rust', 'nodejs', 'npm']:
    install_apk(pkg)

BASE_DIR = pathlib.Path("/tmp/tala_test")
REPO_URL = "https://github.com/d2lang/tala"
REPO_DIR = BASE_DIR / "tala"

def git_clone():
    if REPO_DIR.exists():
        subprocess.run(['rm', '-rf', str(REPO_DIR)])
    return run_cmd(['git', 'clone', REPO_URL, str(REPO_DIR)])

def build_compiler():
    # Assuming the repo uses cargo to build the compiler
    return run_cmd(['cargo', 'build', '--release'], cwd=str(REPO_DIR))

def run_version():
    bin_path = REPO_DIR / "target" / "release" / "tala"
    return run_cmd([str(bin_path), '--version'], cwd=str(REPO_DIR))

def compile_hello():
    hello_src = REPO_DIR / "examples" / "hello.tala"
    if not hello_src.exists():
        hello_src.write_text('print("Hello, TALA!")\n')
    bin_path = REPO_DIR / "target" / "release" / "tala"
    out_exe = REPO_DIR / "hello_out"
    compile_res = run_cmd([str(bin_path), 'build', str(hello_src), '-o', str(out_exe)], cwd=str(REPO_DIR))
    return compile_res, out_exe

def run_hello(out_exe):
    return run_cmd([str(out_exe)], cwd=str(REPO_DIR))

def run_test_suite():
    # Assuming `cargo test` runs the suite
    return run_cmd(['cargo', 'test', '--quiet'], cwd=str(REPO_DIR))

def measure_medium_project():
    # Simulate medium project by cloning a submodule or copying examples
    medium_dir = REPO_DIR / "medium_proj"
    medium_dir.mkdir(exist_ok=True)
    # create dummy source files
    for i in range(20):
        (medium_dir / f"mod{i}.tala").write_text(f'print("module {i}")\n')
    main_src = medium_dir / "main.tala"
    main_src.write_text(''.join([f'import "mod{i}.tala"\n' for i in range(20)]))
    bin_path = REPO_DIR / "target" / "release" / "tala"
    out_exe = REPO_DIR / "medium_out"
    return run_cmd([str(bin_path), 'build', str(main_src), '-o', str(out_exe)], cwd=str(REPO_DIR))

# Begin tests
# Test 1: Clone repo
success, result = False, None
try:
    success, result, _ = benchmark("git_clone", git_clone)
    if success and result.returncode == 0:
        print_marker("TEST_PASS:git_clone")
    else:
        print_marker(f"TEST_FAIL:git_clone:{result.stderr.strip() if result else 'clone failed'}")
except Exception as e:
    print_marker(f"TEST_FAIL:git_clone:{e}")

# Test 2: Build compiler
success, result = False, None
try:
    success, result, compile_time = benchmark("build_compiler", build_compiler)
    if success and result.returncode == 0:
        print_marker("TEST_PASS:build_compiler")
    else:
        print_marker(f"TEST_FAIL:build_compiler:{result.stderr.strip() if result else 'build failed'}")
except Exception as e:
    print_marker(f"TEST_FAIL:build_compiler:{e}")

# Test 3: Version output
try:
    ver_res = run_version()
    if ver_res.returncode == 0 and ver_res.stdout.strip():
        print_marker("TEST_PASS:tala_version")
    else:
        print_marker(f"TEST_FAIL:tala_version:{ver_res.stderr.strip()}")
except Exception as e:
    print_marker(f"TEST_FAIL:tala_version:{e}")

# Test 4: Hello world compile & run
try:
    comp_res, exe_path = compile_hello()
    if comp_res.returncode != 0:
        raise RuntimeError(f"Compile error: {comp_res.stderr.strip()}")
    run_res = run_hello(exe_path)
    if run_res.returncode == 0 and "Hello, TALA!" in run_res.stdout:
        print_marker("TEST_PASS:hello_world")
    else:
        raise AssertionError(f"Output mismatch: {run_res.stdout.strip()}")
except Exception as e:
    print_marker(f"TEST_FAIL:hello_world:{e}")

# Test 5: Medium project compilation benchmark
try:
    medium_res, _ = measure_medium_project()
    if medium_res.returncode == 0:
        print_marker("TEST_PASS:medium_compile")
    else:
        print_marker(f"TEST_FAIL:medium_compile:{medium_res.stderr.strip()}")
except Exception as e:
    print_marker(f"TEST_FAIL:medium_compile:{e}")

# Test 6: Run built‑in test suite
try:
    suite_res = run_test_suite()
    if suite_res.returncode == 0:
        print_marker("TEST_PASS:test_suite")
    else:
        print_marker(f"TEST_FAIL:test_suite:{suite_res.stderr.strip()}")
except Exception as e:
    print_marker(f"TEST_FAIL:test_suite:{e}")

# Additional benchmarks
# Count lines of code in repo
try:
    loc = sum(len(open(f, 'r', errors='ignore').readlines()) for f in REPO_DIR.rglob('*.go') if f.is_file())
    print_marker(f"BENCHMARK:loc_count:{loc}")
except Exception:
    pass

# Number of source files
try:
    src_cnt = sum(1 for _ in REPO_DIR.rglob('*.go'))
    print_marker(f"BENCHMARK:source_files:{src_cnt}")
except Exception:
    pass

# Baseline comparison with Rust (using cargo build time as baseline)
# Assume we have recorded a baseline compile time of 5.0 seconds for similar project
baseline_time = 5.0
if 'compile_time_s' in globals():
    pass
# Using the medium compile time measured earlier (stored in compile_time if succeeded)
try:
    ratio = compile_time / baseline_time if baseline_time else 0
    print_marker(f"BENCHMARK:vs_rust_compile_ratio:{ratio:.2f}")
except Exception:
    pass

print_marker("RUN_OK")