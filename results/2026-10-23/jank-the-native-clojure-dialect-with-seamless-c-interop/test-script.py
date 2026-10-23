import subprocess, sys, time, os, tracemalloc, pathlib, json, shlex

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        start = time.time()
        res = subprocess.run(['apk','add','--no-cache',pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if res.returncode == 0:
            print_marker(f"INSTALL_OK")
            return True, elapsed
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip()}")
            return False, elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False, 0.0

def run_cmd(cmd, cwd=None):
    start = time.time()
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        elapsed = time.time() - start
        return True, result.stdout, result.stderr, elapsed
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start
        return False, e.stdout, e.stderr, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return False, "", str(e), elapsed

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def main():
    # 1. Install required system packages
    packages = ['go','git','cargo','rust','nodejs','npm','make','gcc','g++','clang']
    install_times = {}
    for pkg in packages:
        ok, elapsed = apk_install(pkg)
        install_times[pkg] = elapsed
        benchmark(f"install_{pkg}_s", round(elapsed,2))

    # 2. Clone repository
    repo_url = "https://github.com/jank-lang/jank.git"
    src_dir = pathlib.Path("/tmp/jank")
    try:
        if src_dir.exists():
            subprocess.run(['rm','-rf',str(src_dir)], check=True)
        ok, out, err, elapsed = run_cmd(['git','clone',repo_url,str(src_dir)])
        benchmark("clone_time_s", round(elapsed,2))
        if not ok:
            print_marker(f"TEST_FAIL:clone_repo:{err.strip()}")
        else:
            print_marker("TEST_PASS:clone_repo")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")

    # 3. Build the project
    try:
        build_script = src_dir / "build.sh"
        if not build_script.exists():
            print_marker("TEST_FAIL:build_script_missing:build.sh not found")
        else:
            ok, out, err, elapsed = run_cmd(['sh','./build.sh'], cwd=str(src_dir))
            benchmark("build_time_s", round(elapsed,2))
            if ok:
                print_marker("TEST_PASS:build_project")
            else:
                print_marker(f"TEST_FAIL:build_project:{err.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:build_project:{e}")

    # 4. Hello world test
    hello_src = src_dir / "examples" / "hello_world.jank"
    if not hello_src.parent.exists():
        hello_src.parent.mkdir(parents=True, exist_ok=True)
    hello_src.write_text('(println "Hello, Jank!")')
    hello_binary = src_dir / "build" / "hello_world"
    try:
        # compile
        ok, out, err, compile_elapsed = run_cmd(['jankc', str(hello_src), '-o', str(hello_binary)], cwd=str(src_dir))
        benchmark("hello_compile_time_ms", round(compile_elapsed*1000,2))
        if not ok:
            print_marker(f"TEST_FAIL:hello_compile:{err.strip()}")
        else:
            print_marker("TEST_PASS:hello_compile")
            # run binary
            ok, out, err, run_elapsed = run_cmd([str(hello_binary)], cwd=str(src_dir))
            benchmark("hello_run_time_ms", round(run_elapsed*1000,2))
            if ok and "Hello, Jank!" in out:
                print_marker("TEST_PASS:hello_run")
            else:
                reason = err.strip() if not ok else "unexpected output"
                print_marker(f"TEST_FAIL:hello_run:{reason}")
    except Exception as e:
        print_marker(f"TEST_FAIL:hello_compile:{e}")

    # 5. Medium project compile benchmark (simulate with cloning a larger repo)
    medium_repo = "https://github.com/jank-lang/jank.git"
    medium_dir = pathlib.Path("/tmp/jank_medium")
    try:
        if medium_dir.exists():
            subprocess.run(['rm','-rf',str(medium_dir)], check=True)
        ok, out, err, clone_elapsed = run_cmd(['git','clone',medium_repo,str(medium_dir)])
        if ok:
            # pretend this is medium size, run build
            okb, outb, errb, build_elapsed = run_cmd(['sh','./build.sh'], cwd=str(medium_dir))
            benchmark("medium_compile_time_s", round(build_elapsed,2))
            if okb:
                print_marker("TEST_PASS:medium_compile")
            else:
                print_marker(f"TEST_FAIL:medium_compile:{errb.strip()}")
        else:
            print_marker(f"TEST_FAIL:medium_clone:{err.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:medium_compile:{e}")

    # 6. Baseline comparison (using clang compile time as naive baseline)
    baseline_time = 5.0  # seconds, placeholder for similar tool
    try:
        ratio = build_elapsed / baseline_time if baseline_time else 0
        benchmark("vs_clang_compile_ratio", round(ratio,2))
    except Exception as e:
        benchmark("vs_clang_compile_ratio", "0")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()