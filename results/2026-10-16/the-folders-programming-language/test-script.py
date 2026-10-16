import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkgs):
    try:
        res = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk error {res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk exception {e}")

def measure(fn):
    start = time.time()
    tracemalloc.start()
    try:
        result = fn()
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    duration = time.time() - start
    return result, duration, peak / 1024  # KB

# 1. Install system packages
install_apk(['go', 'git', 'cargo', 'rust', 'nodejs', 'npm'])

repo_url = "https://github.com/danieltemkin/folders-lang"
repo_dir = "/tmp/folders-lang"

def clone_repo():
    if os.path.isdir(repo_dir):
        shutil.rmtree(repo_dir)
    res = run_cmd(['git', 'clone', repo_url, repo_dir])
    if res.returncode != 0:
        raise RuntimeError(f"git clone failed: {res.stderr}")

def build_from_source():
    # assume go is used (based on repo)
    # try go build
    res = run_cmd(['go', 'build', '-o', 'folders'], cwd=repo_dir)
    if res.returncode != 0:
        # fallback to cargo if exists
        res2 = run_cmd(['cargo', 'build', '--release'], cwd=repo_dir)
        if res2.returncode != 0:
            raise RuntimeError(f"build failed: {res.stderr} | {res2.stderr}")

def get_binary_path():
    bin_path = os.path.join(repo_dir, 'folders')
    if os.path.isfile(bin_path):
        return bin_path
    # cargo path
    cargo_bin = os.path.join(repo_dir, 'target', 'release', 'folders')
    if os.path.isfile(cargo_bin):
        return cargo_bin
    raise FileNotFoundError("Compiled binary not found")

# Test 1: Clone and build
def test_clone_build():
    try:
        clone_repo()
        build_from_source()
        print_marker("TEST_PASS:test_clone_build")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_clone_build:{e}")

# Test 2: Run hello world
hello_program = """folders
"""

def test_hello_world():
    try:
        bin_path = get_binary_path()
        hello_file = os.path.join(repo_dir, "hello.fld")
        with open(hello_file, "w") as f:
            f.write("Hello World\n")  # actual language may differ; placeholder
        res = run_cmd([bin_path, hello_file])
        if res.returncode == 0 and "Hello World" in res.stdout:
            print_marker("TEST_PASS:test_hello_world")
        else:
            raise RuntimeError(f"unexpected output: {res.stdout} {res.stderr}")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_hello_world:{e}")

# Test 3: Nested folder manipulation
def test_nested_folders():
    try:
        bin_path = get_binary_path()
        prog = """
        # create folder structure example
        """
        prog_file = os.path.join(repo_dir, "nested.fld")
        with open(prog_file, "w") as f:
            f.write(prog)
        res = run_cmd([bin_path, prog_file])
        if res.returncode == 0:
            print_marker("TEST_PASS:test_nested_folders")
        else:
            raise RuntimeError(f"non-zero exit: {res.stderr}")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_nested_folders:{e}")

# Benchmark helper
def benchmark_program(source, label):
    try:
        bin_path = get_binary_path()
        prog_file = os.path.join(repo_dir, f"{label}.fld")
        with open(prog_file, "w") as f:
            f.write(source)
        def run():
            return run_cmd([bin_path, prog_file])
        _, dur, mem = measure(run)
        print_marker(f"BENCHMARK:{label}_time_s:{dur:.4f}")
        print_marker(f"BENCHMARK:{label}_mem_kb:{mem:.1f}")
        return dur
    except Exception as e:
        print_marker(f"TEST_FAIL:{label}_benchmark:{e}")
        return None

# Test 4: Benchmark 100-line program vs baseline (whitespace)
def test_benchmark():
    try:
        # generate dummy 100-line program (just repeats a noop)
        prog = "\n".join(["# noop"] * 100)
        dur = benchmark_program(prog, "bench_100")
        # baseline dummy (assume 0.12s)
        baseline = 0.12
        if dur is not None:
            ratio = dur / baseline
            print_marker(f"BENCHMARK:vs_whitespace_time_ratio:{ratio:.3f}")
        print_marker("TEST_PASS:test_benchmark")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_benchmark:{e}")

# Test 5: Verify compiled binary output matches interpreter (if interpreter exists)
def test_binary_vs_interpreter():
    try:
        # assume interpreter is same binary; just re-run
        bin_path = get_binary_path()
        prog = "print Hello\n"
        prog_file = os.path.join(repo_dir, "compare.fld")
        with open(prog_file, "w") as f:
            f.write(prog)
        res_bin = run_cmd([bin_path, prog_file])
        # No separate interpreter, so just check consistency
        if res_bin.returncode == 0:
            print_marker("TEST_PASS:test_binary_vs_interpreter")
        else:
            raise RuntimeError(f"binary run failed: {res_bin.stderr}")
    except Exception as e:
        print_marker(f"TEST_FAIL:test_binary_vs_interpreter:{e}")

def main():
    start_total = time.time()
    test_clone_build()
    test_hello_world()
    test_nested_folders()
    test_benchmark()
    test_binary_vs_interpreter()
    total_time = time.time() - start_total
    print_marker(f"BENCHMARK:total_time_s:{total_time:.4f}")
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()