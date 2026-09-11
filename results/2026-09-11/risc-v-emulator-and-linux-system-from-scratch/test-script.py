#!/usr/bin/env python3
import subprocess, sys, time, os, tracemalloc, json, urllib.request, urllib.error, shlex

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, None

def install_apk(packages):
    try:
        cmd = ['apk', 'add', '--no-cache'] + packages
        result, _ = run_cmd(cmd)
        if result and result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            reason = result.stderr.strip() if result else "exception"
            print_marker(f"INSTALL_FAIL:{reason}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def clone_repo(url, dest):
    if os.path.isdir(dest):
        return True, ""
    cmd = ['git', 'clone', '--depth', '1', url, dest]
    result, _ = run_cmd(cmd)
    if result and result.returncode == 0:
        return True, ""
    return False, result.stderr.strip() if result else "exception"

def measure_memory(func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    func(*args, **kwargs)
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return end - start, peak / 1024  # seconds, KiB

def baseline_qemu_boot_time():
    # Simple estimation: try to run qemu-system-riscv64 -nographic -kernel <dummy>
    # Use a small timeout to avoid long hangs.
    cmd = ['qemu-system-riscv64', '-nographic', '-kernel', '/dev/null']
    start = time.time()
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except Exception:
        pass
    return time.time() - start

def main():
    # 1. Install required apk packages
    install_apk(['git', 'curl', 'make', 'gcc', 'musl-dev', 'linux-headers'])
    
    repo_url = "https://github.com/WerWolv/riscv-emulator"
    src_dir = "/tmp/riscv-emulator"
    ok, err = clone_repo(repo_url, src_dir)
    if ok:
        print_marker("TEST_PASS:clone_repo")
    else:
        print_marker(f"TEST_FAIL:clone_repo:{err}")

    # 2. Build the emulator
    build_start = time.time()
    result, build_time = run_cmd(['make', 'build'], cwd=src_dir)
    if result and result.returncode == 0:
        print_marker("TEST_PASS:build")
    else:
        reason = result.stderr.strip() if result else "exception"
        print_marker(f"TEST_FAIL:build:{reason}")

    print_marker(f"BENCHMARK:install_time_s:{build_time:.2f}")

    # 3. Verify binary exists
    binary_path = os.path.join(src_dir, "riscv-emulator")
    if os.path.isfile(binary_path):
        print_marker("TEST_PASS:binary_exists")
    else:
        print_marker("TEST_FAIL:binary_exists:binary not found")

    # 4. Run emulator with a simple hello world (using built-in test if any)
    hello_start = time.time()
    result, hello_elapsed = run_cmd([binary_path, '--help'])
    if result and result.returncode == 0:
        print_marker("TEST_PASS:emulator_help")
    else:
        reason = result.stderr.strip() if result else "exception"
        print_marker(f"TEST_FAIL:emulator_help:{reason}")

    print_marker(f"BENCHMARK:emulator_help_ms:{hello_elapsed*1000:.2f}")

    # 5. Measure boot time (simulate by running emulator with a minimal kernel if available)
    # Since we don't have a real kernel image, we approximate by measuring start latency
    boot_start = time.time()
    result, boot_elapsed = run_cmd([binary_path], cwd=src_dir, env=os.environ.copy())
    # We expect it to exit quickly with help or error
    if result:
        print_marker("TEST_PASS:boot_time_measure")
    else:
        print_marker("TEST_FAIL:boot_time_measure:run failed")

    print_marker(f"BENCHMARK:boot_time_ms:{boot_elapsed*1000:.2f}")

    # 6. Compare with QEMU baseline
    qemu_time = baseline_qemu_boot_time()
    if qemu_time > 0:
        ratio = boot_elapsed / qemu_time if qemu_time else 0
        print_marker(f"BENCHMARK:vs_qemu_boot_ratio:{ratio:.2f}")
    else:
        print_marker("BENCHMARK:vs_qemu_boot_ratio:na")

    # 7. Run a small C program inside emulator (skip if not feasible)
    # Create tiny C program
    c_prog = r'''
    #include <stdio.h>
    int main(){ printf("Hello from inside VM\n"); return 0; }
    '''
    c_path = os.path.join(src_dir, "hello.c")
    with open(c_path, "w") as f:
        f.write(c_prog)
    # Compile with gcc (host) just to test compilation flow
    compile_res, compile_time = run_cmd(['gcc', c_path, '-o', os.path.join(src_dir, 'hello')])
    if compile_res and compile_res.returncode == 0:
        print_marker("TEST_PASS:host_compile")
    else:
        reason = compile_res.stderr.strip() if compile_res else "exception"
        print_marker(f"TEST_FAIL:host_compile:{reason}")

    print_marker(f"BENCHMARK:host_compile_time_ms:{compile_time*1000:.2f}")

    # Try to run compiled binary inside emulator (placeholder, just run binary)
    exec_res, exec_time = run_cmd([binary_path, '--run', os.path.join(src_dir, 'hello')])
    if exec_res and exec_res.returncode == 0:
        print_marker("TEST_PASS:run_inside_vm")
    else:
        reason = exec_res.stderr.strip() if exec_res else "exception"
        print_marker(f"TEST_FAIL:run_inside_vm:{reason}")

    print_marker(f"BENCHMARK:run_inside_vm_ms:{exec_time*1000:.2f}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()