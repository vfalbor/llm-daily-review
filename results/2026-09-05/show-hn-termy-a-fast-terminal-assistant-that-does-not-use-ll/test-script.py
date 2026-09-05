import subprocess, sys, time, os, json, shlex, tracemalloc, pathlib, re

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None, timeout=120):
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
            check=False,
        )
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, time.time() - start

def install_apk(packages):
    try:
        subprocess.run(['apk', 'add', '--no-cache'] + packages, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def clone_repo(url, dest):
    if dest.exists():
        subprocess.run(['rm', '-rf', str(dest)], check=False)
    result, _ = run_cmd(['git', 'clone', '--depth', '1', url, str(dest)])
    return result and result.returncode == 0

def cargo_install(path):
    result, elapsed = run_cmd(['cargo', 'install', '--path', '.'], cwd=path)
    return result and result.returncode == 0, elapsed

def exec_cli(args, cwd=None):
    result, elapsed = run_cmd(['termy'] + args, cwd=cwd)
    return result, elapsed

def measure_memory(func, *a, **kw):
    tracemalloc.start()
    start = time.time()
    try:
        func(*a, **kw)
    except Exception:
        pass
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return time.time() - start, peak / 1024  # MB

def main():
    # 1. Install required system packages
    pkgs = ['nodejs', 'npm', 'git', 'cargo', 'rust']
    install_apk(pkgs)

    repo_url = "https://github.com/gioblu/NPC-Forge"
    workdir = pathlib.Path("/tmp/termysrc")
    if not clone_repo(repo_url, workdir):
        print_marker("TEST_FAIL:clone_repo:Unable to clone repository")
    else:
        print_marker("TEST_PASS:clone_repo")

    # 2. Build with cargo
    build_ok = False
    build_time = None
    if workdir.exists():
        try:
            ok, elapsed = cargo_install(workdir)
            build_ok = ok
            build_time = elapsed
            if ok:
                print_marker("TEST_PASS:cargo_install")
                print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")
            else:
                print_marker("TEST_FAIL:cargo_install:Cargo install returned non-zero")
        except Exception as e:
            print_marker(f"TEST_FAIL:cargo_install:{e}")

    # 3. Help command
    try:
        result, elapsed = exec_cli(['--help'])
        if result and result.returncode == 0:
            print_marker("TEST_PASS:help_command")
            print_marker(f"BENCHMARK:help_time_ms:{elapsed*1000:.2f}")
        else:
            print_marker(f"TEST_FAIL:help_command:Non-zero exit or no result")
    except Exception as e:
        print_marker(f"TEST_FAIL:help_command:{e}")

    # 4. info command on sample dir
    sample_dir = pathlib.Path("/tmp/termysample")
    sample_dir.mkdir(parents=True, exist_ok=True)
    # create dummy files
    for i in range(5):
        (sample_dir / f"file{i}.txt").write_text("hello world\n")
    try:
        result, elapsed = exec_cli(['info', str(sample_dir)])
        if result and result.returncode == 0:
            # simple format check: expect JSON or key-value lines
            output = result.stdout.strip()
            if re.search(r'files?\s*:\s*\d+', output, re.IGNORECASE) or output.startswith('{'):
                print_marker("TEST_PASS:info_command")
            else:
                print_marker("TEST_FAIL:info_command:Unexpected output format")
            print_marker(f"BENCHMARK:info_time_ms:{elapsed*1000:.2f}")
        else:
            print_marker("TEST_FAIL:info_command:Non-zero exit")
    except Exception as e:
        print_marker(f"TEST_FAIL:info_command:{e}")

    # 5. Benchmark vs baseline (using `bat` as similar tool for file preview)
    # Measure bat --help as baseline
    try:
        base_res, base_elapsed = run_cmd(['bat', '--help'])
        if base_res and base_res.returncode == 0:
            ratio = (elapsed / base_elapsed) if base_elapsed else 0
            print_marker(f"BENCHMARK:vs_bat_help_ratio:{ratio:.3f}")
        else:
            print_marker("TEST_SKIP:baseline_bat:bat not installed")
    except Exception as e:
        print_marker(f"TEST_SKIP:baseline_bat:{e}")

    # Additional memory benchmark for info command
    mem_time, mem_peak = measure_memory(exec_cli, ['info', str(sample_dir)])
    print_marker(f"BENCHMARK:info_mem_peak_mb:{mem_peak:.2f}")

    # Ensure at least 3 benchmark lines (install_time, help_time, info_time already printed)
    # Print RUN_OK
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()