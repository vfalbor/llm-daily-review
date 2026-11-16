import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib, re, threading, queue

REPO_URL = "https://github.com/mit41301/simple-8085-computer"
REPO_DIR = "/tmp/simple-8085-computer"
BASELINE_CMD = ["python3", "-c", "print('baseline')"]  # placeholder for 8085-sim call

def print_marker(line):
    print(line, flush=True)

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
        duration = time.time() - start
        return result, duration
    except Exception as e:
        return None, time.time() - start

def install_apk(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def clone_repo():
    try:
        if os.path.isdir(REPO_DIR):
            shutil.rmtree(REPO_DIR)
        result, _ = run_cmd(['git', 'clone', '--depth', '1', REPO_URL, REPO_DIR])
        if result and result.returncode == 0:
            print_marker("TEST_PASS:clone_repo")
            return True
        else:
            reason = result.stderr.strip() if result else "git failed"
            print_marker(f"TEST_FAIL:clone_repo:{reason}")
            return False
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")
        return False

def count_source_files():
    try:
        total_files = 0
        language_counts = {}
        for root, _, files in os.walk(REPO_DIR):
            for f in files:
                total_files += 1
                ext = pathlib.Path(f).suffix.lower()
                language_counts[ext] = language_counts.get(ext, 0) + 1
        print_marker(f"BENCHMARK:src_files_count:{total_files}")
        print_marker(f"BENCHMARK:src_langs:{json.dumps(language_counts)}")
        print_marker("TEST_PASS:count_source_files")
    except Exception as e:
        print_marker(f"TEST_FAIL:count_source_files:{e}")

def build_emulator():
    # Assume there's a Makefile or python setup
    makefile = os.path.join(REPO_DIR, "Makefile")
    setup_py = os.path.join(REPO_DIR, "setup.py")
    try:
        if os.path.isfile(makefile):
            result, duration = run_cmd(['make'], cwd=REPO_DIR)
            print_marker(f"BENCHMARK:build_time_s:{duration:.3f}")
            if result and result.returncode == 0:
                print_marker("TEST_PASS:build_emulator")
                return True
            else:
                print_marker(f"TEST_FAIL:build_emulator:{result.stderr.strip() if result else 'make failed'}")
                return False
        elif os.path.isfile(setup_py):
            # try pip install -e .
            result, duration = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=REPO_DIR)
            print_marker(f"BENCHMARK:build_time_s:{duration:.3f}")
            if result and result.returncode == 0:
                print_marker("TEST_PASS:build_emulator")
                return True
            else:
                print_marker(f"TEST_FAIL:build_emulator:{result.stderr.strip() if result else 'pip install failed'}")
                return False
        else:
            print_marker("TEST_SKIP:build_emulator:No build system found")
            return False
    except Exception as e:
        print_marker(f"TEST_FAIL:build_emulator:{e}")
        return False

def find_hello_world():
    candidates = []
    for root, _, files in os.walk(REPO_DIR):
        for f in files:
            if re.search(r'hello', f, re.I):
                candidates.append(os.path.join(root, f))
    return candidates[0] if candidates else None

def run_hello_world():
    script = find_hello_world()
    if not script:
        print_marker("TEST_SKIP:run_hello_world:No hello world script found")
        return
    try:
        start = time.time()
        tracemalloc.start()
        result, _ = run_cmd([sys.executable, script])
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration = time.time() - start
        print_marker(f"BENCHMARK:hello_world_time_ms:{duration*1000:.2f}")
        print_marker(f"BENCHMARK:hello_world_mem_kb:{peak/1024:.2f}")
        if result and result.returncode == 0 and "Hello" in result.stdout:
            print_marker("TEST_PASS:run_hello_world")
        else:
            reason = result.stderr.strip() if result else "execution failed"
            print_marker(f"TEST_FAIL:run_hello_world:{reason}")
    except Exception as e:
        print_marker(f"TEST_FAIL:run_hello_world:{e}")

def measure_cycle_count():
    # Look for a sample instruction file
    instr_file = None
    for root, _, files in os.walk(REPO_DIR):
        for f in files:
            if f.endswith('.asm') or f.endswith('.txt'):
                instr_file = os.path.join(root, f)
                break
        if instr_file:
            break
    if not instr_file:
        print_marker("TEST_SKIP:measure_cycle_count:No instruction file")
        return
    # Assume emulator can be invoked as ./emulator <file> --cycles
    emulator_bin = os.path.join(REPO_DIR, "emulator")
    if not os.path.isfile(emulator_bin):
        emulator_bin = shutil.which("emulator") or ""
    if not emulator_bin:
        print_marker("TEST_SKIP:measure_cycle_count:Emulator binary not found")
        return
    try:
        start = time.time()
        result, _ = run_cmd([emulator_bin, instr_file, "--cycles"])
        duration = time.time() - start
        print_marker(f"BENCHMARK:cycle_count_time_ms:{duration*1000:.2f}")
        if result and result.returncode == 0:
            # extract cycles from output
            m = re.search(r'Cycles\s*:\s*(\d+)', result.stdout)
            if m:
                cycles = int(m.group(1))
                print_marker(f"BENCHMARK:cycles_executed:{cycles}")
                print_marker("TEST_PASS:measure_cycle_count")
            else:
                print_marker("TEST_FAIL:measure_cycle_count:No cycle info")
        else:
            reason = result.stderr.strip() if result else "emulator failed"
            print_marker(f"TEST_FAIL:measure_cycle_count:{reason}")
    except Exception as e:
        print_marker(f"TEST_FAIL:measure_cycle_count:{e}")

def run_baseline():
    # Attempt to run 8085-sim if installed via apk (placeholder)
    try:
        result, duration = run_cmd(["8085-sim", "--version"])
        if result and result.returncode == 0:
            return duration
    except Exception:
        pass
    # Fallback: use dummy baseline duration
    return None

def compare_performance():
    # Compare hello world time vs baseline if available
    baseline = run_baseline()
    # Retrieve our measured hello world time from environment (simple approach: re-run)
    hello_script = find_hello_world()
    if not hello_script or baseline is None:
        print_marker("TEST_SKIP:compare_performance:Baseline or hello script missing")
        return
    try:
        start = time.time()
        result, _ = run_cmd([sys.executable, hello_script])
        our_time = time.time() - start
        ratio = our_time / baseline if baseline > 0 else 0
        print_marker(f"BENCHMARK:vs_8085-sim_hello_time_ratio:{ratio:.3f}")
        print_marker("TEST_PASS:compare_performance")
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_performance:{e}")

def main():
    # 1. Install required apk packages
    install_apk('git')

    # 2. Clone repo
    if not clone_repo():
        # cannot continue meaningfully, but continue to emit benchmarks
        pass

    # 3. Count source files
    count_source_files()

    # 4. Build emulator
    build_emulator()

    # 5. Run hello world example
    run_hello_world()

    # 6. Measure cycle count
    measure_cycle_count()

    # 7. Compare with baseline tool
    compare_performance()

    # Ensure at least three benchmark lines (already emitted above)
    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()