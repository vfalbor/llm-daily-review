import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_apk(packages):
    start = time.time()
    rc, out, err = run_cmd(['apk', 'add', '--no-cache'] + packages)
    elapsed = time.time() - start
    if rc == 0:
        print(f"INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{err.strip() or 'apk install error'}")
    print(f"BENCHMARK:install_time_s:{elapsed:.2f}")

def install_toolchain():
    # Already installed via apk step (nodejs, npm, git, cargo, rust)
    pass

def clone_sdcc():
    repo = "https://github.com/sdcc/sdcc.git"
    dst = "/tmp/sdcc"
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', repo, dst])
    if rc != 0:
        raise RuntimeError(f"git clone failed: {err}")
    return dst

def build_sdcc(src_dir):
    start = time.time()
    rc, out, err = run_cmd(['./configure', '--prefix=/usr/local'], cwd=src_dir)
    if rc != 0:
        raise RuntimeError(f"configure failed: {err}")
    rc, out, err = run_cmd(['make', '-j2'], cwd=src_dir)
    if rc != 0:
        raise RuntimeError(f"make failed: {err}")
    rc, out, err = run_cmd(['make', 'install'], cwd=src_dir)
    if rc != 0:
        raise RuntimeError(f"make install failed: {err}")
    elapsed = time.time() - start
    print(f"BENCHMARK:build_time_s:{elapsed:.2f}")

def test_hello_world():
    test_name = "hello_world_compile"
    workdir = "/tmp/sdcc_test"
    os.makedirs(workdir, exist_ok=True)
    hello_c = """#include <stdio.h>
int main() {
    printf("Hello, SDCC!\\n");
    return 0;
}
"""
    src_path = os.path.join(workdir, "hello.c")
    with open(src_path, "w") as f:
        f.write(hello_c)
    out_hex = os.path.join(workdir, "hello.hex")
    start = time.time()
    rc, out, err = run_cmd(['sdcc', '-o', out_hex, src_path], cwd=workdir)
    compile_time = time.time() - start
    print(f"BENCHMARK:{test_name}_time_s:{compile_time:.2f}")
    if rc != 0:
        print(f"TEST_FAIL:{test_name}:{err.strip()}")
        return
    # Use sdcc's simulator for 8051 if available
    sim_cmd = ['s51', out_hex]  # s51 is the 8051 simulator shipped with sdcc
    rc, out, err = run_cmd(sim_cmd, cwd=workdir)
    if rc != 0:
        print(f"TEST_FAIL:{test_name}:run error {err.strip()}")
        return
    if "Hello, SDCC!" in out:
        print(f"TEST_PASS:{test_name}")
    else:
        print(f"TEST_FAIL:{test_name}:unexpected output")

def benchmark_modern_project():
    test_name = "moderate_project_compile"
    workdir = "/tmp/sdcc_mod_proj"
    os.makedirs(workdir, exist_ok=True)
    # Create multiple source files
    for i in range(10):
        src = f"""int func{i}(int x) {{ return x + {i}; }}
"""
        with open(os.path.join(workdir, f"mod{i}.c"), "w") as f:
            f.write(src)
    main_c = """#include <stdio.h>
int main() {
    int sum = 0;
"""
    for i in range(10):
        main_c += f"    sum += func{i}(i);\n"
    main_c += """    printf("Sum=%d\\n", sum);
    return 0;
}
"""
    with open(os.path.join(workdir, "main.c"), "w") as f:
        f.write(main_c)
    start = time.time()
    rc, out, err = run_cmd(['sdcc', '-o', 'mod.hex', 'main.c'] + [f"mod{i}.c" for i in range(10)], cwd=workdir)
    elapsed = time.time() - start
    print(f"BENCHMARK:{test_name}_time_s:{elapsed:.2f}")
    if rc != 0:
        print(f"TEST_FAIL:{test_name}:compile error {err.strip()}")
        return
    print(f"TEST_PASS:{test_name}")

def baseline_tinycc():
    # Install tinycc via apk (if available) and measure a simple compile
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', 'tinycc'])
    if rc != 0:
        print("TEST_SKIP:baseline_tinycc:apk install failed")
        return None
    workdir = "/tmp/tinycc_test"
    os.makedirs(workdir, exist_ok=True)
    src = """int main(){return 0;}"""
    src_path = os.path.join(workdir, "a.c")
    with open(src_path, "w") as f:
        f.write(src)
    start = time.time()
    rc, out, err = run_cmd(['tcc', '-o', 'a.out', src_path], cwd=workdir)
    elapsed = time.time() - start
    if rc != 0:
        print("TEST_SKIP:baseline_tinycc:compile failed")
        return None
    return elapsed

def compare_with_baseline():
    sdcc_time = None
    # Extract last sdcc compile benchmark
    # For simplicity re-run a small compile
    workdir = "/tmp/sdcc_cmp"
    os.makedirs(workdir, exist_ok=True)
    src = "int main(){return 0;}"
    src_path = os.path.join(workdir, "b.c")
    with open(src_path, "w") as f:
        f.write(src)
    start = time.time()
    rc, out, err = run_cmd(['sdcc', '-o', 'b.hex', src_path], cwd=workdir)
    if rc == 0:
        sdcc_time = time.time() - start
    tiny_time = baseline_tinycc()
    if sdcc_time is not None and tiny_time is not None and tiny_time > 0:
        ratio = sdcc_time / tiny_time
        print(f"BENCHMARK:vs_tinycc_compile_ratio:{ratio:.2f}")

def main():
    # 1. Install required apk packages
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust', 'make', 'gcc', 'musl-dev', 'autoconf', 'automake', 'libtool'])
    # 2. Clone and build sdcc
    try:
        src_dir = clone_sdcc()
        build_sdcc(src_dir)
        print("TEST_PASS:install_sdcc")
    except Exception as e:
        print(f"TEST_FAIL:install_sdcc:{e}")
    # 3. Test hello world compile and run
    try:
        test_hello_world()
    except Exception as e:
        print(f"TEST_FAIL:hello_world_compile:{e}")
    # 4. Benchmark moderate project compile
    try:
        benchmark_modern_project()
    except Exception as e:
        print(f"TEST_FAIL:moderate_project_compile:{e}")
    # 5. Compare with baseline tool
    try:
        compare_with_baseline()
    except Exception as e:
        print(f"TEST_FAIL:compare_with_baseline:{e}")
    # 6. Emit final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()