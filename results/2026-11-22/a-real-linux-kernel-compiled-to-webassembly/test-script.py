import subprocess, sys, os, time, tracemalloc, hashlib, shutil, json

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def apk_install(pkg):
    start = time.time()
    try:
        result = run_cmd(['apk', 'add', '--no-cache', pkg])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        print_marker(f"INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    finally:
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:apk_{pkg}_install_s:{elapsed:.3f}")

def git_clone(repo, dest):
    start = time.time()
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        result = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    finally:
        print_marker(f"BENCHMARK:git_clone_s:{time.time()-start:.3f}")

def build_unkernel(src_dir):
    start = time.time()
    try:
        # The repo provides a Makefile; use it
        result = run_cmd(['make'], cwd=src_dir)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    finally:
        print_marker(f"BENCHMARK:build_s:{time.time()-start:.3f}")

def measure_file(path):
    try:
        size = os.path.getsize(path)
        print_marker(f"BENCHMARK:wasm_size_bytes:{size}")
        return size
    except Exception as e:
        print_marker(f"TEST_FAIL:measure_file:{e}")
        return None

def run_wasm(runtime, wasm_path, args=None):
    cmd = [runtime, wasm_path] + (args or [])
    start = time.time()
    try:
        result = run_cmd(cmd)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        print_marker(f"TEST_PASS:run_{runtime}")
        return result.stdout.strip()
    except Exception as e:
        print_marker(f"TEST_FAIL:run_{runtime}:{e}")
        return None
    finally:
        print_marker(f"BENCHMARK:{runtime}_exec_s:{time.time()-start:.3f}")

def compile_hello_world(src_dir, out_wasm):
    start = time.time()
    try:
        # Use wasi-sdk clang if present, fallback to clang from apk (installed earlier)
        clang = shutil.which('clang')
        if not clang:
            raise RuntimeError("clang not found")
        result = run_cmd([clang, '--target=wasm32-wasi', '-O2', '-o', out_wasm,
                         os.path.join(src_dir, 'hello.c')])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        print_marker("TEST_PASS:compile_hello")
    except Exception as e:
        print_marker(f"TEST_FAIL:compile_hello:{e}")
    finally:
        print_marker(f"BENCHMARK:hello_compile_s:{time.time()-start:.3f}")

def main():
    # 1. Install required system packages
    for pkg in ['go', 'git', 'cargo', 'rust', 'nodejs', 'npm', 'wasmtime']:
        apk_install(pkg)

    # 2. Clone repository
    repo_url = 'https://github.com/pithings/unkernel'
    src_dir = '/tmp/unkernel'
    git_clone(repo_url, src_dir)

    # 3. Build the kernel
    build_unkernel(src_dir)

    # locate produced wasm (assume ./unkernel.wasm)
    wasm_path = os.path.join(src_dir, 'unkernel.wasm')
    if not os.path.isfile(wasm_path):
        # fallback: look for any .wasm in src_dir
        matches = [f for f in os.listdir(src_dir) if f.endswith('.wasm')]
        if matches:
            wasm_path = os.path.join(src_dir, matches[0])
        else:
            print_marker("TEST_FAIL:find_wasm:wasm binary not found")
            wasm_path = None

    # 4. Run kernel with wasmtime and perform simple syscalls test
    if wasm_path:
        output = run_wasm('wasmtime', wasm_path, ['--invoke', 'main'])
        # Expect some output like "Hello from unkernel"
        if output and "Hello" in output:
            print_marker("TEST_PASS:kernel_hello_output")
        else:
            print_marker(f"TEST_FAIL:kernel_hello_output:unexpected output {output}")

    # 5. Benchmark size vs native baseline (approx 2.5 MB)
    wasm_size = measure_file(wasm_path) if wasm_path else None
    native_baseline = 2_500_000  # bytes (example)
    if wasm_size:
        ratio = wasm_size / native_baseline
        print_marker(f"BENCHMARK:vs_native_kernel_size_ratio:{ratio:.3f}")

    # 6. Compile a tiny Hello World program to Wasm
    hello_c = """
    #include <stdio.h>
    int main(){ printf("Hello World\\n"); return 0; }
    """
    hello_dir = '/tmp/hello'
    os.makedirs(hello_dir, exist_ok=True)
    hello_c_path = os.path.join(hello_dir, 'hello.c')
    with open(hello_c_path, 'w') as f:
        f.write(hello_c)
    hello_wasm = os.path.join(hello_dir, 'hello.wasm')
    compile_hello_world(hello_dir, hello_wasm)

    # 7. Run Hello World inside the unkernel (assuming unkernel can load modules via args)
    if wasm_path and os.path.isfile(hello_wasm):
        out = run_wasm('wasmtime', wasm_path, ['--', hello_wasm])
        if out and "Hello World" in out:
            print_marker("TEST_PASS:hello_inside_kernel")
        else:
            print_marker(f"TEST_FAIL:hello_inside_kernel:output {out}")

    # 8. Compare runtime against wasmtime baseline for a simple wasm (e.g., fib)
    # create small fib wasm using wasmtime compile (placeholder)
    fib_wasm = os.path.join(hello_dir, 'fib.wasm')
    # generate via wat2wasm if available, else skip
    wat2wasm = shutil.which('wat2wasm')
    if wat2wasm:
        fib_wat = "(module (func (export \"fib\") (param i32) (result i32) (local.get 0)))"
        wat_path = os.path.join(hello_dir, 'fib.wat')
        with open(wat_path, 'w') as f:
            f.write(fib_wat)
        run_cmd([wat2wasm, wat_path, '-o', fib_wasm])
        t_start = time.time()
        run_wasm('wasmtime', fib_wasm)
        wasmtime_time = time.time() - t_start
        print_marker(f"BENCHMARK:wasmtime_fib_exec_s:{wasmtime_time:.3f}")
        # compare with unkernel execution if possible
        if wasm_path:
            t_start = time.time()
            run_wasm('wasmtime', wasm_path, ['--', fib_wasm])
            unkernel_time = time.time() - t_start
            ratio = unkernel_time / wasmtime_time if wasmtime_time else 0
            print_marker(f"BENCHMARK:vs_wasmtime_fib_ratio:{ratio:.3f}")

    # Ensure at least three benchmark lines (already emitted many)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()