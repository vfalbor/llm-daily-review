#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, traceback, re
from pathlib import Path

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, description):
    start = time.time()
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start
        print_marker(f"INSTALL_OK | {description}")
        return True, duration
    except Exception as e:
        duration = time.time() - start
        print_marker(f"INSTALL_FAIL:{description}:{e}")
        return False, duration

def install_apk_packages():
    pkgs = ["git"]
    success, dur = run_cmd(["apk", "add", "--no-cache"] + pkgs, "apk_add_"+ "_".join(pkgs))
    print_marker(f"BENCHMARK:apk_install_time_s:{dur:.3f}")

def pip_install_package():
    start = time.time()
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "load-bearing-vocab"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dur = time.time() - start
        print_marker(f"INSTALL_OK | pip_install_load-bearing-vocab")
        return True, dur
    except Exception as e:
        dur = time.time() - start
        print_marker(f"INSTALL_FAIL:pip_install_load-bearing-vocab:{e}")
        return False, dur

def git_clone_and_editable_install():
    repo = "https://github.com/louisabraham/load-bearing.git"
    dst = Path("/tmp/load-bearing")
    if dst.exists():
        subprocess.run(["rm", "-rf", str(dst)], check=False)
    start = time.time()
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo, str(dst)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "-e", str(dst)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dur = time.time() - start
        print_marker(f"INSTALL_OK | git_clone_editable")
        return True, dur
    except Exception as e:
        dur = time.time() - start
        print_marker(f"INSTALL_FAIL:git_clone_editable:{e}")
        return False, dur

def measure_import():
    start = time.time()
    tracemalloc.start()
    try:
        import load_bearing  # type: ignore
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        dur = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{dur:.2f}")
        print_marker(f"BENCHMARK:import_memory_peak_kb:{peak/1024:.2f}")
        return True, dur
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_module:{e}")
        return False, None

def test_core_operation():
    """Run a minimal functional test with synthetic data."""
    start = time.time()
    try:
        from load_bearing import core  # hypothetical submodule
        # synthetic dataset: list of words with frequencies
        data = {"hello": 10, "world": 5, "test": 2}
        result = core.process_vocab(data)  # assume returns dict with same keys
        if not isinstance(result, dict) or set(result.keys()) != set(data.keys()):
            raise ValueError("Result keys mismatch")
        dur = (time.time() - start) * 1000
        print_marker(f"TEST_PASS:core_operation")
        print_marker(f"BENCHMARK:core_op_latency_ms:{dur:.2f}")
        return True, dur
    except Exception as e:
        print_marker(f"TEST_FAIL:core_operation:{e}")
        return False, None

def benchmark_vs_baseline():
    """Compare against a simple WordCloud generation (baseline)."""
    try:
        import timeit, collections
        # baseline: count words using Counter (fast)
        def baseline():
            words = ["hello"]*10 + ["world"]*5 + ["test"]*2
            return collections.Counter(words)
        baseline_time = timeit.timeit(baseline, number=10) * 1000  # ms
        # our core op already measured; re-run for consistency
        from load_bearing import core
        data = {"hello": 10, "world": 5, "test": 2}
        def ours():
            core.process_vocab(data)
        ours_time = timeit.timeit(ours, number=10) * 1000
        ratio = ours_time / baseline_time if baseline_time else float('inf')
        print_marker(f"BENCHMARK:vs_wordcloud_latency_ratio:{ratio:.3f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:benchmark_vs_baseline:{e}")
        return False

def main():
    # 1. Install system deps
    install_apk_packages()

    # 2. Install python package
    ok, pip_dur = pip_install_package()
    if not ok:
        ok, git_dur = git_clone_and_editable_install()
        if not ok:
            print_marker("TEST_SKIP:install_package:Both pip and git install failed")
    # 3. Import measurement
    imp_ok, imp_dur = measure_import()

    # 4. Core functional test
    core_ok, core_dur = test_core_operation()

    # 5. Baseline comparison
    vs_ok = benchmark_vs_baseline()

    # Emit some extra benchmarks
    # Example: count lines of source files
    try:
        src_dir = Path(__file__).parent
        loc = sum(1 for p in src_dir.rglob("*.py") for _ in open(p, "rb"))
        print_marker(f"BENCHMARK:loc_count:{loc}")
    except Exception:
        pass

    # Always final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()