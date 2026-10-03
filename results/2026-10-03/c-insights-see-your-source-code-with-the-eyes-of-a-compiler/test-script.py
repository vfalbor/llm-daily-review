#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib, hashlib

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None, capture=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=True,
        )
        return (0, result.stdout if capture else "")
    except subprocess.CalledProcessError as e:
        return (e.returncode, e.stderr if capture else "")

def install_apk(pkg):
    rc, _ = run_cmd(['apk', 'add', '--no-cache', pkg])
    return rc == 0

def timed(func):
    start = time.time()
    rc = func()
    elapsed = time.time() - start
    return rc, elapsed

# 1. Install system packages
pkgs = ['nodejs', 'npm', 'git', 'cargo', 'rust']
install_fail = []
for p in pkgs:
    if not install_apk(p):
        install_fail.append(p)
if install_fail:
    marker(f"INSTALL_FAIL:apk_packages={' '.join(install_fail)}")
else:
    marker("INSTALL_OK")

# 2. Clone repo and build
repo_url = "https://github.com/andreasfertig/cppinsights.git"
workdir = pathlib.Path("/tmp/cppinsights_test")
if workdir.exists():
    shutil.rmtree(workdir)
workdir.mkdir(parents=True)

def clone_repo():
    return run_cmd(['git', 'clone', '--depth', '1', repo_url, str(workdir)])

rc, _ = clone_repo()
if rc != 0:
    marker("TEST_FAIL:clone_repo:git clone failed")
else:
    marker("TEST_PASS:clone_repo")

# 3. Build with cargo
def cargo_build():
    return run_cmd(['cargo', 'build', '--release'], cwd=str(workdir))

rc, _ = cargo_build()
if rc != 0:
    marker("TEST_FAIL:build:cargo build failed")
else:
    marker("TEST_PASS:build")

# Path to binary
binary_path = workdir / "target" / "release" / "cppinsights"
if not binary_path.is_file():
    marker("TEST_FAIL:binary_missing:Binary not found after build")
    # abort further tests that need binary
    binary_path = None

# Benchmark install time (approx)
# Using a simple measure of git clone + cargo build time
def benchmark_install():
    start = time.time()
    # re-clone into a temp dir and build
    tmp = pathlib.Path("/tmp/cppinsights_bench")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    rc, _ = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(tmp)])
    if rc != 0:
        return None
    rc, _ = run_cmd(['cargo', 'build', '--release'], cwd=str(tmp))
    if rc != 0:
        return None
    return time.time() - start

install_time = benchmark_install()
if install_time is not None:
    marker(f"BENCHMARK:install_time_s:{install_time:.2f}")

# 4. Test --help
if binary_path:
    rc, out = run_cmd([str(binary_path), '--help'], capture=True)
    if rc == 0 and "Usage" in out:
        marker("TEST_PASS:help")
    else:
        marker("TEST_FAIL:help:Help output not as expected")
else:
    marker("TEST_SKIP:help:binary missing")

# 5. Simple hello world test
hello_cpp = workdir / "hello.cpp"
hello_cpp.write_text('#include <iostream>\nint main(){std::cout<<"Hello";return 0;}\n')
if binary_path:
    rc, out = run_cmd([str(binary_path), str(hello_cpp)], capture=True)
    if rc == 0 and "Hello" in out:
        marker("TEST_PASS:hello_world")
    else:
        marker(f"TEST_FAIL:hello_world:Unexpected output or error")
else:
    marker("TEST_SKIP:hello_world:binary missing")

# 6. Benchmark execution on 10kB file
large_cpp = workdir / "large.cpp"
# generate roughly 10KB of simple code
lines = []
for i in range(200):
    lines.append(f'void func{i}() {{ int a{i}=0; a{i}++; }}')
large_cpp.write_text('\n'.join(lines))

def run_cppinsights(file_path):
    start = time.time()
    rc, out = run_cmd([str(binary_path), str(file_path)], capture=True)
    elapsed = time.time() - start
    return rc, out, elapsed

if binary_path:
    rc, out, elapsed = run_cppinsights(large_cpp)
    marker(f"BENCHMARK:large_file_ms:{elapsed*1000:.2f}")
    if rc == 0 and elapsed <= 5.0:
        marker("TEST_PASS:large_file_time")
    else:
        reason = "timeout" if elapsed > 5.0 else "non-zero exit"
        marker(f"TEST_FAIL:large_file_time:{reason}")
else:
    marker("TEST_SKIP:large_file_time:binary missing")

# 7. Multi-file project test
proj_dir = workdir / "proj"
proj_dir.mkdir()
(main_cpp := proj_dir / "main.cpp").write_text('#include "a.h"\nint main(){return foo();}\n')
(a_h := proj_dir / "a.h").write_text('int foo();\n')
(a_cpp := proj_dir / "a.cpp").write_text('#include "a.h"\nint foo(){return 42;}\n')

if binary_path:
    rc, out = run_cmd([str(binary_path), str(main_cpp)], capture=True)
    if rc == 0 and "return 42" in out:
        marker("TEST_PASS:multi_file")
    else:
        marker("TEST_FAIL:multi_file:Output missing or error")
else:
    marker("TEST_SKIP:multi_file:binary missing")

# 8. Memory usage benchmark (tracemalloc)
tracemalloc.start()
start = time.time()
if binary_path:
    rc, out = run_cmd([str(binary_path), str(hello_cpp)], capture=True)
    elapsed = time.time() - start
    current, peak = tracemalloc.get_traced_memory()
    marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    marker(f"BENCHMARK:hello_exec_ms:{elapsed*1000:.2f}")
    if rc != 0:
        marker("TEST_FAIL:hello_mem:execution failed")
    else:
        marker("TEST_PASS:hello_mem")
tracemalloc.stop()

# 9. Baseline comparison with clangd (assuming clangd is installed via apk)
# Install clangd if not present
if not shutil.which("clangd"):
    install_apk('clang-tools-extra')
# simple benchmark: run clangd --version (fast) vs cppinsights help
def bench_tool(cmd):
    start = time.time()
    rc, _ = run_cmd(cmd, capture=True)
    return time.time() - start

clangd_time = bench_tool(['clangd', '--version'])
cppinsights_time = bench_tool([str(binary_path), '--help']) if binary_path else None
if clangd_time and cppinsights_time:
    ratio = cppinsights_time / clangd_time if clangd_time else 0
    marker(f"BENCHMARK:vs_clangd_help_ratio:{ratio:.2f}")

# Ensure at least 3 benchmark lines emitted (already emitted several)
marker("RUN_OK")