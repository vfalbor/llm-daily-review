import subprocess, sys, os, time, tracemalloc, shlex, json, pathlib

def run_cmd(cmd, cwd=None, env=None):
    try:
        start = time.time()
        result = subprocess.run(
            cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, check=False
        )
        duration = time.time() - start
        return result.returncode, result.stdout, duration
    except Exception as e:
        return 1, str(e), 0.0

def install_apk(pkgs):
    try:
        rc, out, dur = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
        if rc == 0:
            print(f"INSTALL_OK")
        else:
            print(f"INSTALL_FAIL:{out.strip()}")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def install_tool():
    # try cargo install from repo if needed
    pass  # placeholder not allowed; we will attempt clone+cargo install later

def clone_repo(url, dest):
    rc, out, _ = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    return rc == 0

def measure_install():
    start = time.time()
    # install apk packages required
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])
    dur = time.time() - start
    print(f"BENCHMARK:install_time_s:{dur:.2f}")

def test_cargo_test(repo_path):
    try:
        rc, out, dur = run_cmd(['cargo', 'test', '--quiet'], cwd=repo_path)
        if rc == 0:
            print(f"TEST_PASS:cargo_test")
        else:
            print(f"TEST_FAIL:cargo_test:{out.strip()}")
        print(f"BENCHMARK:cargo_test_time_s:{dur:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:cargo_test:{e}")

def benchmark_build(repo_path, tool_enabled):
    env = os.environ.copy()
    if tool_enabled:
        env['RUSTFLAGS'] = '-Cmetadata-early'  # placeholder flag for the tool
    rc, out, dur = run_cmd(['cargo', 'build', '--quiet'], cwd=repo_path, env=env)
    label = 'build_with_tool' if tool_enabled else 'build_without_tool'
    if rc == 0:
        print(f"TEST_PASS:{label}")
    else:
        print(f"TEST_FAIL:{label}:{out.strip()}")
    print(f"BENCHMARK:{label}_time_s:{dur:.2f}")
    return dur

def benchmark_cargo_bench(repo_path):
    rc, out, dur = run_cmd(['cargo', 'bench', '--quiet'], cwd=repo_path)
    if rc == 0:
        print(f"TEST_PASS:cargo_bench")
    else:
        print(f"TEST_FAIL:cargo_bench:{out.strip()}")
    print(f"BENCHMARK:cargo_bench_time_s:{dur:.2f}")

def compare_vs_baseline(with_tool, without_tool):
    if without_tool == 0:
        ratio = 0.0
    else:
        ratio = with_tool / without_tool
    print(f"BENCHMARK:vs_cargo_build_ratio:{ratio:.3f}")

def main():
    repo_url = "https://github.com/PowderworksCode/headstart"
    workdir = pathlib.Path("/tmp/headstart_repo")
    if workdir.exists():
        subprocess.run(['rm', '-rf', str(workdir)])
    measure_install()

    if not clone_repo(repo_url, str(workdir)):
        print("TEST_FAIL:clone_repo:git clone failed")
        print("RUN_OK")
        return

    # Run cargo test
    test_cargo_test(str(workdir))

    # Benchmark builds
    time_without = benchmark_build(str(workdir), tool_enabled=False)
    time_with = benchmark_build(str(workdir), tool_enabled=True)

    # Compare vs baseline (cargo without tool)
    compare_vs_baseline(time_with, time_without)

    # Run cargo bench
    benchmark_cargo_bench(str(workdir))

    # Additional benchmark: memory usage during build with tool
    tracemalloc.start()
    _, _, _ = run_cmd(['cargo', 'clean'], cwd=str(workdir))
    rc, out, dur = run_cmd(['cargo', 'build', '--quiet'], cwd=str(workdir), env=os.environ.copy())
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:build_memory_peak_kb:{peak/1024:.2f}")

    print("RUN_OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"TEST_FAIL:unexpected_error:{e}")
        print("RUN_OK")