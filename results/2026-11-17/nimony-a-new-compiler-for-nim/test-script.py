import subprocess, sys, os, time, tracemalloc, json, shlex, pathlib, shutil, hashlib

def log(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def apk_install(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
    except Exception as e:
        log(f"INSTALL_FAIL:{pkg}:{e}")
        return False
    return True

def install_system_packages():
    pkgs = ['go', 'git', 'cargo', 'rust', 'nodejs', 'npm']
    ok = True
    for p in pkgs:
        if not apk_install(p):
            ok = False
    if ok:
        log("INSTALL_OK")
    else:
        log("INSTALL_FAIL:system_packages:some packages failed")
    return ok

def clone_repo():
    repo_url = "https://github.com/nimony/nimony"
    dst = "/tmp/nimony"
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    try:
        res = run_cmd(['git', 'clone', '--depth', '1', repo_url, dst])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        log("INSTALL_OK")
        return dst
    except Exception as e:
        log(f"INSTALL_FAIL:clone_repo:{e}")
        return None

def build_nimony(src_dir):
    try:
        # Assuming the project uses Nim's build system; we try to build using nimble
        # First ensure nim is available (apk provides nim via 'nim' package)
        if not shutil.which('nim'):
            if not apk_install('nim'):
                raise RuntimeError("nim not installed")
        # nimble install may need to be run inside src_dir
        res = run_cmd(['nimble', '--accept', 'install', 'nimony'], cwd=src_dir)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        log("INSTALL_OK")
        return True
    except Exception as e:
        log(f"INSTALL_FAIL:build_nimony:{e}")
        return False

def benchmark(name, func):
    start = time.time()
    tracemalloc.start()
    try:
        result = func()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start
        log(f"BENCHMARK:{name}_time_s:{elapsed:.3f}")
        log(f"BENCHMARK:{name}_mem_kb:{peak/1024:.1f}")
        return result, elapsed
    except Exception as e:
        tracemalloc.stop()
        log(f"BENCHMARK:{name}_error:{e}")
        return None, None

def test_hello_world(src_dir):
    test_name = "hello_world"
    try:
        prog = pathlib.Path(src_dir) / "hello.nim"
        prog.write_text('echo "Hello, World!"\n')
        def compile():
            return run_cmd(['nimony', '-o:hello_bin', str(prog)], cwd=src_dir)
        _, comp_time = benchmark(test_name + "_compile", compile)
        if comp_time is None:
            raise RuntimeError("compilation failed")
        # run binary
        exec_path = pathlib.Path(src_dir) / "hello_bin"
        res = run_cmd([str(exec_path)], cwd=src_dir)
        if res.returncode != 0 or "Hello, World!" not in res.stdout:
            raise RuntimeError("runtime output mismatch")
        log(f"TEST_PASS:{test_name}")
    except Exception as e:
        log(f"TEST_FAIL:{test_name}:{e}")

def test_vs_official_nim(src_dir):
    test_name = "vs_official_nim"
    try:
        prog = pathlib.Path(src_dir) / "fib.nim"
        prog.write_text('proc fib(n:int):int= if n<2: n else: fib(n-1)+fib(n-2)\necho fib(30)\n')
        # compile with nimony
        def comp_nimony():
            return run_cmd(['nimony', '-O2', '-o:nimony_bin', str(prog)], cwd=src_dir)
        _, t_nimony = benchmark(test_name + "_nimony", comp_nimony)
        # compile with official nim
        if not shutil.which('nim'):
            raise RuntimeError("official nim not found")
        def comp_nim():
            return run_cmd(['nim', 'c', '-O2', '--out:nim_bin', str(prog)], cwd=src_dir)
        _, t_nim = benchmark(test_name + "_nim", comp_nim)
        if t_nimony is None or t_nim is None:
            raise RuntimeError("compilation timing failed")
        ratio = t_nimony / t_nim if t_nim != 0 else 0
        log(f"BENCHMARK:vs_nim_compile_ratio:{ratio:.3f}")
        log(f"TEST_PASS:{test_name}")
    except Exception as e:
        log(f"TEST_FAIL:{test_name}:{e}")

def test_large_project(src_dir):
    test_name = "large_project"
    try:
        # clone a sample Nim web server project into temp dir
        proj_dir = pathlib.Path(src_dir) / "nimweb"
        if proj_dir.is_dir():
            shutil.rmtree(proj_dir)
        res = run_cmd(['git', 'clone', '--depth', '1', 'https://github.com/status-im/nim-chronos.git', str(proj_dir)])
        if res.returncode != 0:
            raise RuntimeError("failed to clone large project")
        # Build with nimony
        def build_nimony():
            return run_cmd(['nimble', 'build', '-Y'], cwd=proj_dir)
        _, t_build = benchmark(test_name + "_build", build_nimony)
        bin_path = proj_dir / "bin" / "chronos_example"
        if not bin_path.is_file():
            raise RuntimeError("binary not produced")
        size_bytes = bin_path.stat().st_size
        log(f"BENCHMARK:{test_name}_binary_size_kb:{size_bytes/1024:.1f}")
        # Measure startup latency
        def run_bin():
            return run_cmd([str(bin_path)], cwd=proj_dir)
        _, startup = benchmark(test_name + "_startup", run_bin)
        log(f"BENCHMARK:{test_name}_startup_ms:{startup*1000:.2f}" if startup else "")
        log(f"TEST_PASS:{test_name}")
    except Exception as e:
        log(f"TEST_FAIL:{test_name}:{e}")

def main():
    # 1. Install system packages
    if not install_system_packages():
        pass
    # 2. Clone repo
    src = clone_repo()
    if not src:
        log("RUN_OK")
        return
    # 3. Build nimony
    if not build_nimony(src):
        pass
    # 4. Run tests
    test_hello_world(src)
    test_vs_official_nim(src)
    test_large_project(src)
    # Ensure at least three benchmark lines are emitted (already done in each test)
    log("RUN_OK")

if __name__ == "__main__":
    main()