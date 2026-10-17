#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json

def run_cmd(cmd, cwd=None, env=None):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return e, None

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkgs):
    try:
        res, t = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
        if isinstance(res, Exception) or res.returncode != 0:
            reason = (res.stderr.strip() if not isinstance(res, Exception) else str(res))
            print_marker(f"INSTALL_FAIL:{reason}")
            return False, t
        print_marker("INSTALL_OK")
        return True, t
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False, None

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def main():
    # 1. Install system packages
    ok, install_time = install_apk(['go', 'git', 'cargo', 'rust', 'nodejs', 'npm'])
    if install_time is not None:
        benchmark('install_time_s', round(install_time, 2))
    else:
        benchmark('install_time_s', -1)

    # 2. Clone repository
    repo_url = "https://github.com/lf-lang/lf-lang"
    workdir = "/tmp/lf-lang"
    if os.path.isdir(workdir):
        shutil.rmtree(workdir)
    clone_start = time.time()
    try:
        res, _ = run_cmd(['git', 'clone', '--depth', '1', repo_url, workdir])
        if isinstance(res, Exception) or res.returncode != 0:
            raise RuntimeError(res.stderr.strip() if not isinstance(res, Exception) else str(res))
        benchmark('clone_time_s', round(time.time() - clone_start, 2))
        print_marker("TEST_PASS:git_clone")
    except Exception as e:
        print_marker(f"TEST_FAIL:git_clone:{e}")

    # 3. Build from source (make install)
    build_time = None
    try:
        tracemalloc.start()
        res, elapsed = run_cmd(['make', 'install'], cwd=workdir)
        if isinstance(res, Exception) or res.returncode != 0:
            raise RuntimeError(res.stderr.strip() if not isinstance(res, Exception) else str(res))
        build_time = elapsed
        benchmark('build_time_s', round(build_time, 2))
        print_marker("TEST_PASS:make_install")
    except Exception as e:
        print_marker(f"TEST_FAIL:make_install:{e}")
        if build_time is None:
            benchmark('build_time_s', -1)

    # 4. Compile hello world using lfc
    hello_src = os.path.join(workdir, "examples", "hello.lf")
    if not os.path.isfile(hello_src):
        # create minimal hello.lf if not present
        os.makedirs(os.path.dirname(hello_src), exist_ok=True)
        with open(hello_src, "w") as f:
            f.write('println("Hello, LF!")\n')
    hello_exe = os.path.join(workdir, "hello")
    compile_time = None
    try:
        start = time.time()
        res, _ = run_cmd(['lfc', '-o', hello_exe, hello_src], cwd=workdir)
        if isinstance(res, Exception) or res.returncode != 0:
            raise RuntimeError(res.stderr.strip() if not isinstance(res, Exception) else str(res))
        compile_time = time.time() - start
        benchmark('hello_compile_time_s', round(compile_time, 2))
        print_marker("TEST_PASS:compile_hello")
    except Exception as e:
        print_marker(f"TEST_FAIL:compile_hello:{e}")
        benchmark('hello_compile_time_s', -1)

    # 5. Run hello executable
    try:
        start = time.time()
        res, _ = run_cmd([hello_exe], cwd=workdir)
        if isinstance(res, Exception) or res.returncode != 0:
            raise RuntimeError(res.stderr.strip() if not isinstance(res, Exception) else str(res))
        run_time = time.time() - start
        benchmark('hello_run_time_ms', round(run_time * 1000, 2))
        print_marker("TEST_PASS:run_hello")
    except Exception as e:
        print_marker(f"TEST_FAIL:run_hello:{e}")
        benchmark('hello_run_time_ms', -1)

    # Baseline comparison against Go compile time (approx 1.2s)
    baseline_go_compile = 1.2
    if compile_time is not None:
        ratio = round(compile_time / baseline_go_compile, 3)
        benchmark('vs_go_compile_time_ratio', ratio)
    else:
        benchmark('vs_go_compile_time_ratio', -1)

    # Additional benchmarks
    # Memory usage during compile
    if compile_time is not None:
        current, peak = tracemalloc.get_traced_memory()
        benchmark('compile_peak_memory_kb', round(peak/1024, 2))
    tracemalloc.stop()

    # Count of source files
    try:
        total_files = sum(len(files) for _, _, files in os.walk(workdir))
        benchmark('source_files_count', total_files)
    except Exception:
        benchmark('source_files_count', -1)

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()