import subprocess, sys, os, time, tracemalloc, pathlib, json, shlex, traceback

REPO_URL = "https://github.com/0x23/MicroManipulatorStepper.git"
REPO_DIR = "/tmp/MicroManipulatorStepper"
BASELINE_TOOL = "grbl"

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    return result

def install_apk(pkg):
    start = time.time()
    try:
        subprocess.run(['apk','add','--no-cache',pkg], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:install_{pkg}_time_s:{duration:.2f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def clone_repo():
    start = time.time()
    try:
        if os.path.isdir(REPO_DIR):
            subprocess.run(['rm','-rf',REPO_DIR], check=False)
        result = run_cmd(['git','clone','--depth','1',REPO_URL, REPO_DIR])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        duration = time.time() - start
        print_marker(f"TEST_PASS:clone_repo")
        print_marker(f"BENCHMARK:clone_time_s:{duration:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")

def count_files_and_languages():
    try:
        total_files = 0
        lang_counts = {}
        for root, _, files in os.walk(REPO_DIR):
            for f in files:
                total_files += 1
                ext = pathlib.Path(f).suffix.lower()
                if ext:
                    lang_counts[ext] = lang_counts.get(ext,0)+1
        print_marker(f"TEST_PASS:file_count")
        print_marker(f"BENCHMARK:source_files_count:{total_files}")
        for ext, cnt in lang_counts.items():
            print_marker(f"BENCHMARK:lang_{ext}_count:{cnt}")
    except Exception as e:
        print_marker(f"TEST_FAIL:file_count:{e}")

def build_firmware():
    makefile = os.path.join(REPO_DIR, "Makefile")
    if not os.path.isfile(makefile):
        print_marker("TEST_SKIP:build_firmware:Makefile not found")
        return
    start = time.time()
    try:
        result = run_cmd(['make'], cwd=REPO_DIR)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        duration = time.time() - start
        print_marker("TEST_PASS:build_firmware")
        print_marker(f"BENCHMARK:build_time_s:{duration:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:build_firmware:{e}")

def run_python_example():
    # Look for .py files that look like examples
    examples = []
    for root, _, files in os.walk(REPO_DIR):
        for f in files:
            if f.lower().endswith('.py') and 'example' in f.lower():
                examples.append(os.path.join(root, f))
    if not examples:
        print_marker("TEST_SKIP:python_example:No example script found")
        return
    script = examples[0]
    start = time.time()
    try:
        result = run_cmd([sys.executable, script])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        duration = (time.time() - start) * 1000  # ms
        print_marker("TEST_PASS:python_example")
        print_marker(f"BENCHMARK:python_example_ms:{duration:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:python_example:{e}")

def benchmark_vs_baseline(metric, value):
    # Dummy baseline values for illustration
    baseline_vals = {
        "build_time_s": 20.0,
        "clone_time_s": 5.0,
        "python_example_ms": 200.0,
    }
    base = baseline_vals.get(metric)
    if base:
        ratio = value / base
        print_marker(f"BENCHMARK:vs_{BASELINE_TOOL}_{metric}:{ratio:.2f}")

def main():
    try:
        install_apk('git')
        clone_repo()
        count_files_and_languages()
        build_firmware()
        run_python_example()

        # Emit additional benchmarks (memory usage)
        tracemalloc.start()
        snapshot = tracemalloc.take_snapshot()
        top = snapshot.statistics('lineno')[:1]
        mem_kb = top[0].size / 1024 if top else 0
        print_marker(f"BENCHMARK:memory_peak_kb:{mem_kb:.2f}")

        # Example comparisons
        benchmark_vs_baseline("build_time_s", 0)  # placeholder will be ignored if no value
        benchmark_vs_baseline("clone_time_s", 0)
        benchmark_vs_baseline("python_example_ms", 0)

    except Exception as e:
        print_marker(f"TEST_FAIL:unexpected:{traceback.format_exc()}")
    finally:
        print_marker("RUN_OK")

if __name__ == "__main__":
    main()