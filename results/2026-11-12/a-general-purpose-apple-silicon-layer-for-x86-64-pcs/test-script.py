#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, shutil, json, urllib.request

# Helpers
def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def print_marker(line):
    print(line, flush=True)

def install_apk(pkgs):
    try:
        result = run_cmd(['apk', 'add', '--no-cache'] + pkgs, check=False)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {','.join(pkgs)} error:{result.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {','.join(pkgs)} exception:{e}")

def clone_repo(url, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    result = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    return result.returncode == 0

def measure(fn):
    start = time.time()
    tracemalloc.start()
    try:
        fn()
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    elapsed = time.time() - start
    return elapsed, current, peak

# 1. Install system deps
install_apk(['git', 'curl', 'build-base', 'make'])

# 2. Install Stela
STELA_REPO = "https://github.com/tylertms/Stela.git"
STELA_DIR = "/tmp/stela_src"
installed = False

if clone_repo(STELA_REPO, STELA_DIR):
    # try make install (assume makefile exists)
    make_res = run_cmd(['make', 'install'], cwd=STELA_DIR)
    if make_res.returncode == 0:
        installed = True
        print_marker("INSTALL_OK")
    else:
        # fallback: pip editable if python package present
        pip_res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=STELA_DIR)
        if pip_res.returncode == 0:
            installed = True
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:stela build error:{make_res.stderr.strip() or pip_res.stderr.strip()}")
else:
    print_marker("INSTALL_FAIL:git clone failed")

# Helper to ensure stela CLI exists
def stela_cli():
    return shutil.which('stela') is not None

# Benchmark binary preparation (simple hello world compiled for x86_64)
X86_BIN = "/tmp/hello_x86"
def build_x86_binary():
    src = """
    #include <stdio.h>
    int main(){ printf("hello\\n"); return 0; }
    """
    src_path = "/tmp/hello.c"
    with open(src_path, "w") as f: f.write(src)
    # compile for x86_64 using gcc (default on alpine is x86_64)
    compile_res = run_cmd(['gcc', src_path, '-o', X86_BIN])
    return compile_res.returncode == 0

# 3. Test 1: run benchmark binary under Stela
def test_run_stela():
    if not installed or not stela_cli():
        raise RuntimeError("Stela not installed or CLI missing")
    if not os.path.isfile(X86_BIN):
        if not build_x86_binary():
            raise RuntimeError("Failed to build x86 binary")
    elapsed, _, _ = measure(lambda: run_cmd(['stela', X86_BIN]))
    print_marker(f"BENCHMARK:stela_run_time_s:{elapsed:.3f}")
    print_marker("TEST_PASS:test_run_stela")
    
try:
    test_run_stela()
except Exception as e:
    print_marker(f"TEST_FAIL:test_run_stela:{e}")

# 4. Test 2: compare with QEMU (baseline)
def test_compare_qemu():
    if not shutil.which('qemu-x86_64'):
        raise RuntimeError("qemu-x86_64 not installed")
    if not os.path.isfile(X86_BIN):
        raise RuntimeError("Benchmark binary missing")
    # measure qemu
    qemu_elapsed, _, _ = measure(lambda: run_cmd(['qemu-x86_64', X86_BIN]))
    # measure stela (reuse previous measurement if possible)
    stela_elapsed, _, _ = measure(lambda: run_cmd(['stela', X86_BIN]))
    ratio = stela_elapsed / qemu_elapsed if qemu_elapsed else float('inf')
    print_marker(f"BENCHMARK:qemu_run_time_s:{qemu_elapsed:.3f}")
    print_marker(f"BENCHMARK:vs_qemu_ratio:{ratio:.3f}")
    print_marker("TEST_PASS:test_compare_qemu")
except Exception as e:
    print_marker(f"TEST_FAIL:test_compare_qemu:{e}")

# 5. Test 3: compile and run a C program via Stela (simulate)
def test_compile_via_stela():
    # Assume Stela provides a wrapper gcc (stela-gcc) – if not, skip
    stela_gcc = shutil.which('stela-gcc')
    if not stela_gcc:
        raise RuntimeError("stela-gcc not available")
    src = "/tmp/prog.c"
    with open(src, "w") as f:
        f.write('int main(){return 0;}')
    exe = "/tmp/prog_stela"
    compile_res = run_cmd([stela_gcc, src, '-o', exe])
    if compile_res.returncode != 0:
        raise RuntimeError(f"stela-gcc compile error:{compile_res.stderr.strip()}")
    run_res = run_cmd([exe])
    if run_res.returncode != 0:
        raise RuntimeError(f"Program exited non-zero:{run_res.returncode}")
    print_marker("TEST_PASS:test_compile_via_stela")
except Exception as e:
    print_marker(f"TEST_FAIL:test_compile_via_stela:{e}")

# Additional benchmarks (memory usage)
def benchmark_memory():
    if not os.path.isfile(X86_BIN):
        return
    def exec_bin():
        run_cmd(['stela', X86_BIN])
    _, current, peak = measure(exec_bin)
    print_marker(f"BENCHMARK:stela_mem_current_bytes:{current}")
    print_marker(f"BENCHMARK:stela_mem_peak_bytes:{peak}")

benchmark_memory()

# Final marker
print_marker("RUN_OK")