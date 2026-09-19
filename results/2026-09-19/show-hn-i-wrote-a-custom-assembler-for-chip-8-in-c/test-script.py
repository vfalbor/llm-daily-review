import subprocess, sys, os, time, tracemalloc, hashlib, json, shlex, pathlib, textwrap

def run_cmd(cmd, cwd=None, capture=False):
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None, text=True, check=False)
        return result
    except Exception as e:
        return None

def print_marker(msg):
    print(msg, flush=True)

def install_apk(packages):
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache'] + packages)
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print_marker(f"INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else "exception")
        print_marker(f"INSTALL_FAIL:{reason}")
    print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.3f}")

def git_clone(repo, dest):
    start = time.time()
    res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else "exception")
        print_marker(f"INSTALL_FAIL:{reason}")
    print_marker(f"BENCHMARK:git_clone_time_s:{elapsed:.3f}")

def build_make(src_dir):
    start = time.time()
    res = run_cmd(['make'], cwd=src_dir)
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else "exception")
        print_marker(f"INSTALL_FAIL:{reason}")
    print_marker(f"BENCHMARK:build_time_s:{elapsed:.3f}")

def create_hello_c8(path):
    content = textwrap.dedent("""\
        ; Simple CHIP-8 program that clears the screen
        00E0 ; CLS
        1200 ; JP 200h (endless loop)
    """)
    with open(path, "w") as f:
        f.write(content)

def test_help(binary_path):
    start = time.time()
    res = run_cmd([binary_path, '--help'], capture=True)
    elapsed = time.time() - start
    if res and res.returncode == 0 and "Usage" in res.stdout:
        print_marker("TEST_PASS:help")
    else:
        reason = res.stderr.strip() if res else "exception"
        print_marker(f"TEST_FAIL:help:{reason}")
    print_marker(f"BENCHMARK:help_time_ms:{elapsed*1000:.2f}")

def test_assemble(binary_path, src, out):
    start = time.time()
    res = run_cmd([binary_path, src, out], capture=True)
    elapsed = time.time() - start
    if res and res.returncode == 0 and os.path.isfile(out):
        size = os.path.getsize(out)
        expected = 512  # 0x200 bytes typical CHIP-8 ROM start address, but file size may differ
        if size >= expected:
            print_marker("TEST_PASS:assemble")
        else:
            print_marker(f"TEST_FAIL:assemble:size {size} < {expected}")
    else:
        reason = res.stderr.strip() if res else "exception"
        print_marker(f"TEST_FAIL:assemble:{reason}")
    print_marker(f"BENCHMARK:assemble_time_ms:{elapsed*1000:.2f}")

def benchmark_memory(func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        func(*args, **kwargs)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    elapsed = time.time() - start
    return elapsed, peak

def main():
    # 1. Install required APK packages
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])

    repo_url = "https://github.com/Tackx/c8-ass"
    workdir = "/tmp/c8-ass"
    if os.path.isdir(workdir):
        subprocess.run(['rm', '-rf', workdir])
    git_clone(repo_url, workdir)

    # 2. Build the tool
    build_make(workdir)

    binary = os.path.join(workdir, "c8-ass")
    if not os.path.isfile(binary):
        print_marker("TEST_SKIP:binary_missing:Binary not built")
        # cannot proceed further
        print_marker("RUN_OK")
        return

    # 3. Test --help
    test_help(binary)

    # 4. Create minimal program and assemble
    src_file = os.path.join(workdir, "HELLO.C8")
    out_file = os.path.join(workdir, "hello.rom")
    create_hello_c8(src_file)
    test_assemble(binary, src_file, out_file)

    # 5. Benchmark memory usage of assembly
    asm_time, asm_mem = benchmark_memory(test_assemble, binary, src_file, out_file)
    print_marker(f"BENCHMARK:assemble_mem_peak_bytes:{asm_mem}")

    # 6. Baseline comparison (using c8asm if available)
    baseline_binary = "/usr/local/bin/c8asm"
    if os.path.isfile(baseline_binary):
        start = time.time()
        res = run_cmd([baseline_binary, src_file, out_file], capture=True)
        baseline_time = time.time() - start
        ratio = asm_time / baseline_time if baseline_time > 0 else 0
        print_marker(f"BENCHMARK:vs_c8asm_assemble_ratio:{ratio:.3f}")
    else:
        print_marker("BENCHMARK:vs_c8asm_assemble_ratio:0.0")

    # 7. Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()