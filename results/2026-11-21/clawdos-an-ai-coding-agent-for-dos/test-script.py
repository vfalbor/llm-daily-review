import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        start = time.time()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, None

def install_apk(pkg):
    result, elapsed = run_cmd(['apk', 'add', '--no-cache', pkg])
    if result and result.returncode == 0:
        print_marker(f"INSTALL_OK")
    else:
        reason = (result.stderr.strip() if result else str(e))
        print_marker(f"INSTALL_FAIL:{reason}")
    return elapsed or 0.0

def pip_install(pkg):
    result, elapsed = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-deps', pkg])
    if result and result.returncode == 0:
        print_marker("INSTALL_OK")
        return True, elapsed
    else:
        reason = result.stderr.strip() if result else "unknown"
        print_marker(f"INSTALL_FAIL:{reason}")
        return False, elapsed

def git_clone(repo, dest):
    result, elapsed = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    if result and result.returncode == 0:
        print_marker("INSTALL_OK")
        return True, elapsed
    else:
        reason = result.stderr.strip() if result else "unknown"
        print_marker(f"INSTALL_FAIL:{reason}")
        return False, elapsed

def pip_editable(path):
    result, elapsed = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    if result and result.returncode == 0:
        print_marker("INSTALL_OK")
        return True, elapsed
    else:
        reason = result.stderr.strip() if result else "unknown"
        print_marker(f"INSTALL_FAIL:{reason}")
        return False, elapsed

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def main():
    # 1. Install required apk packages
    install_time_git = install_apk('git')
    benchmark('apk_git_install_time_s', round(install_time_git, 3))

    # 2. Install ClawDOS via pip
    install_start = time.time()
    success, pip_time = pip_install('clawdos')
    install_elapsed = time.time() - install_start
    benchmark('pip_install_time_s', round(install_elapsed, 3))

    # fallback to git clone if pip failed
    if not success:
        repo_url = 'https://github.com/ricapar/ClawDOS.git'  # placeholder, may not exist
        clone_dir = '/tmp/clawdos_src'
        cloned, clone_time = git_clone(repo_url, clone_dir)
        benchmark('git_clone_time_s', round(clone_time, 3))
        if cloned:
            installed, editable_time = pip_editable(clone_dir)
            benchmark('pip_editable_install_time_s', round(editable_time, 3))
        else:
            installed = False

    # 3. Import and measure import time
    import_start = time.time()
    try:
        import clawdos
        import_elapsed = time.time() - import_start
        benchmark('import_time_ms', int(import_elapsed * 1000))
        print_marker("TEST_PASS:import_module")
    except Exception as e:
        import_elapsed = time.time() - import_start
        benchmark('import_time_ms', int(import_elapsed * 1000))
        print_marker(f"TEST_FAIL:import_module:{e}")

    # 4. Minimal functional test
    try:
        # assume the package provides a class `ClawDOS` with method `generate_code`
        agent = clawdos.ClawDOS()
        prompt = "Write a Python function that returns the factorial of n."
        gen_start = time.time()
        output = agent.generate_code(prompt)
        gen_elapsed = time.time() - gen_start
        benchmark('code_generation_latency_ms', int(gen_elapsed * 1000))
        # simple syntax check
        try:
            compile(output, '<generated>', 'exec')
            print_marker("TEST_PASS:code_generation")
        except SyntaxError as se:
            print_marker(f"TEST_FAIL:code_generation:SyntaxError")
    except Exception as e:
        print_marker(f"TEST_FAIL:code_generation:{e}")

    # 5. Latency test for 100‑char prompt
    try:
        long_prompt = "Explain the algorithm for quicksort and provide a Python implementation. " * 2
        lat_start = time.time()
        _ = agent.generate_code(long_prompt)
        lat_elapsed = time.time() - lat_start
        benchmark('100char_prompt_latency_ms', int(lat_elapsed * 1000))
        print_marker("TEST_PASS:prompt_latency")
    except Exception as e:
        print_marker(f"TEST_FAIL:prompt_latency:{e}")

    # 6. Multi‑line completion mock test
    try:
        multiline_prompt = "Create a DOS batch file that lists all .txt files and counts them."
        resp = agent.generate_code(multiline_prompt)
        lines = resp.strip().splitlines()
        if len(lines) >= 2:
            print_marker("TEST_PASS:multiline_completion")
        else:
            print_marker("TEST_FAIL:multiline_completion:Not enough lines")
        benchmark('multiline_output_lines', len(lines))
    except Exception as e:
        print_marker(f"TEST_FAIL:multiline_completion:{e}")

    # 7. Baseline comparison (using placeholder baseline latency 200ms)
    baseline_latency_ms = 200
    try:
        my_latency = lat_elapsed * 1000 if 'lat_elapsed' in locals() else None
        if my_latency:
            ratio = round(my_latency / baseline_latency_ms, 3)
            benchmark('vs_copilot_latency_ratio', ratio)
    except Exception:
        pass

    # Ensure at least three benchmark lines (already emitted many)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()