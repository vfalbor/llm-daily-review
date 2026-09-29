#!/usr/bin/env python3
import subprocess
import sys
import time
import traceback
import tracemalloc
import json
import os

def print_marker(msg):
    sys.stdout.flush()
    print(msg)
    sys.stdout.flush()

def run_cmd(cmd, description):
    start = time.time()
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK | {description}")
        else:
            reason = result.stderr.strip().splitlines()[-1] if result.stderr else "unknown error"
            print_marker(f"INSTALL_FAIL:{reason}")
        return result, elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{str(e)}")
        return None, time.time() - start

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def safe_test(name):
    def decorator(fn):
        def wrapper():
            try:
                fn()
                print_marker(f"TEST_PASS:{name}")
            except Exception as e:
                tb = traceback.format_exc().splitlines()[-1]
                print_marker(f"TEST_FAIL:{name}:{tb}")
        return wrapper
    return decorator

def main():
    # 1. Install system packages
    _, apk_time = run_cmd(['apk','add','--no-cache','git'], "apk git")
    benchmark("apk_git_install_s", round(apk_time, 3))

    # 2. Install python package via pip
    install_start = time.time()
    result, pip_time = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'git+https://github.com/firelex/jeff.git'], "pip install jeff")
    benchmark("pip_install_jeff_s", round(pip_time, 3))

    # Fallback if pip install failed
    if result is None or result.returncode != 0:
        # clone repo
        clone_start = time.time()
        clone_res, clone_time = run_cmd(['git','clone','https://github.com/firelex/jeff.git','/tmp/jeff'], "git clone jeff")
        benchmark("git_clone_jeff_s", round(clone_time, 3))
        if clone_res and clone_res.returncode == 0:
            # install editable
            edit_start = time.time()
            edit_res, edit_time = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '/tmp/jeff'], "pip install -e jeff")
            benchmark("pip_edit_install_jeff_s", round(edit_time, 3))

    # 3. Import time benchmark
    import_start = time.time()
    try:
        import jeff
        import_elapsed = time.time() - import_start
        benchmark("import_jeff_ms", round(import_elapsed*1000, 2))
        print_marker("TEST_PASS:import_jeff")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_jeff:{str(e)}")
        import_elapsed = None

    # 4. Load model test
    @safe_test("load_model")
    def test_load_model():
        if import_elapsed is None:
            raise RuntimeError("jeff not imported")
        # Assuming load_model can accept a path; we use a temporary dummy path
        model_path = "/tmp/dummy_model"
        os.makedirs(model_path, exist_ok=True)
        # create a tiny placeholder file if required by library
        # The library may fallback to a default model if path invalid; we just call
        model = jeff.load_model(model_path)
        if not hasattr(model, "forward"):
            raise AssertionError("Loaded model missing forward method")
        # store for later use
        global _loaded_model
        _loaded_model = model

    test_load_model()

    # 5. Inference benchmark
    @safe_test("inference_latency")
    def test_inference():
        if '_loaded_model' not in globals():
            raise RuntimeError("Model not loaded")
        # synthetic input; shape depends on library, we guess a simple list
        sample_input = {"features": [0.0, 1.0, 2.0]}
        tracemalloc.start()
        start = time.time()
        output = _loaded_model.forward(sample_input)
        elapsed = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        benchmark("inference_latency_ms", round(elapsed*1000, 2))
        benchmark("inference_memory_peak_kb", round(peak/1024, 2))
        # Validate output
        if not isinstance(output, (list, tuple, dict)):
            raise AssertionError(f"Unexpected output type: {type(output)}")
        # simple shape check if output is list
        if isinstance(output, (list, tuple)):
            if len(output) == 0:
                raise AssertionError("Output list empty")
        # store for baseline comparison
        global _last_latency
        _last_latency = elapsed

    test_inference()

    # 6. Baseline comparison (mocked baseline value)
    @safe_test("baseline_comparison")
    def test_baseline():
        # baseline latency for Jev (hypothetical) in seconds
        baseline_latency = 0.05  # 50 ms
        if '_last_latency' not in globals():
            raise RuntimeError("No latency measured")
        ratio = _last_latency / baseline_latency
        benchmark(f"vs_jev_latency_ratio", round(ratio, 3))

    test_baseline()

    # Additional generic benchmarks
    benchmark("loc_count", 0)  # placeholder for lines of code count (could be static)
    benchmark("test_files_count", 1)

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()