import subprocess, sys, time, tracemalloc, os, json, math, shutil, tempfile

def print_marker(line):
    print(line, flush=True)

def install_apk_packages():
    start = time.time()
    try:
        result = subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            reason = result.stderr.decode().strip() or "unknown error"
            print_marker(f"INSTALL_FAIL:{reason}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
    finally:
        duration = time.time() - start
        print_marker(f"BENCHMARK:apk_git_install_time_s:{duration:.3f}")

def pip_install_package():
    start = time.time()
    try:
        # try pip install directly (package name guessed from repo)
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'doomformer'], check=False,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            raise RuntimeError(result.stderr.decode().strip())
    except Exception as e:
        # fallback: git clone + editable install
        try:
            tmp_dir = tempfile.mkdtemp()
            repo_url = "https://github.com/mottopanikeiku/doomformer.git"
            clone_res = subprocess.run(['git', 'clone', '--depth', '1', repo_url, tmp_dir],
                                       check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if clone_res.returncode != 0:
                raise RuntimeError(clone_res.stderr.decode().strip())
            install_res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', tmp_dir],
                                         check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if install_res.returncode != 0:
                raise RuntimeError(install_res.stderr.decode().strip())
            print_marker("INSTALL_OK")
        except Exception as e2:
            print_marker(f"INSTALL_FAIL:{e2}")
    finally:
        duration = time.time() - start
        print_marker(f"BENCHMARK:pip_install_time_s:{duration:.3f}")

def measure_import():
    start = time.time()
    tracemalloc.start()
    try:
        import doomformer  # type: ignore
        print_marker("TEST_PASS:import")
    except Exception as e:
        print_marker(f"TEST_FAIL:import:{e}")
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        duration_ms = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:import_time_ms:{duration_ms:.2f}")
        print_marker(f"BENCHMARK:import_memory_peak_kb:{peak/1024:.2f}")

def run_minimal_inference():
    start = time.time()
    try:
        from doomformer import DoomTransformer  # type: ignore
        # synthetic dummy input: random tensor shape (batch, seq_len, feature)
        import numpy as np
        dummy_obs = np.random.rand(1, 10, 64).astype(np.float32)
        model = DoomTransformer()
        actions = model.generate(dummy_obs)  # assume generate method
        if not isinstance(actions, (list, np.ndarray)):
            raise ValueError("Unexpected actions type")
        print_marker("TEST_PASS:inference")
    except Exception as e:
        print_marker(f"TEST_FAIL:inference:{e}")
    finally:
        duration_ms = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:inference_latency_ms:{duration_ms:.2f}")

def validate_sequence():
    start = time.time()
    try:
        from doomformer import validate_actions  # hypothetical helper
        # Use same dummy actions from previous step if possible
        dummy_actions = [0, 1, 2, 3]  # placeholder valid actions
        valid = validate_actions(dummy_actions)
        if not valid:
            raise ValueError("Sequence invalid")
        print_marker("TEST_PASS:validate_sequence")
    except Exception as e:
        print_marker(f"TEST_FAIL:validate_sequence:{e}")
    finally:
        print_marker(f"BENCHMARK:validate_time_ms:{(time.time()-start)*1000:.2f}")

def benchmark_random_policy():
    start = time.time()
    try:
        import numpy as np
        # Simulate random policy latency
        random_actions = np.random.randint(0, 5, size=10)
        # Assume doomformer has a function to compute latency of a policy
        from doomformer import compute_latency  # hypothetical
        latency = compute_latency(random_actions)
        # baseline random latency (hardcoded for demonstration)
        baseline = 150.0  # ms
        ratio = latency / baseline if baseline else float('nan')
        print_marker(f"TEST_PASS:baseline_random")
        print_marker(f"BENCHMARK:random_policy_latency_ms:{latency:.2f}")
        print_marker(f"BENCHMARK:vs_random_policy_latency_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_random:{e}")
    finally:
        print_marker(f"BENCHMARK:benchmark_random_time_ms:{(time.time()-start)*1000:.2f}")

def main():
    install_apk_packages()
    pip_install_package()
    measure_import()
    run_minimal_inference()
    validate_sequence()
    benchmark_random_policy()
    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()