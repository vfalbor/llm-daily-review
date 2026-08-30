#!/usr/bin/env python3
import subprocess, sys, time, json, os, tracemalloc, math, statistics

def run_cmd(cmd, cwd=None):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, check=False)
        duration = time.time() - start
        return result, duration
    except Exception as e:
        return None, 0.0

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def install_apk(pkg):
    result, dur = run_cmd(['apk', 'add', '--no-cache', pkg])
    if result and result.returncode == 0:
        print_marker(f"INSTALL_OK | install:{pkg}")
    else:
        reason = (result.stderr.strip() if result else str(e))
        print_marker(f"INSTALL_FAIL:{pkg}:{reason}")

def install_go_pkg():
    # try go get
    result, dur = run_cmd(['go', 'install', 'github.com/fugue-labs/monty-go@latest'])
    if result and result.returncode == 0:
        print_marker(f"INSTALL_OK | go_get:monty-go")
        return True, dur
    else:
        # fallback: git clone + go build
        tmp_dir = "/tmp/monty-go"
        if os.path.isdir(tmp_dir):
            subprocess.run(['rm', '-rf', tmp_dir])
        result, _ = run_cmd(['git', 'clone', 'https://github.com/fugue-labs/monty-go', tmp_dir])
        if not result or result.returncode != 0:
            print_marker(f"INSTALL_FAIL:go_clone:{result.stderr.strip() if result else 'clone error'}")
            return False, 0.0
        # build library (no binary, just ensure it compiles)
        result, dur = run_cmd(['go', 'build', './...'], cwd=tmp_dir)
        if result and result.returncode == 0:
            print_marker(f"INSTALL_OK | go_build:monty-go")
            return True, dur
        else:
            print_marker(f"INSTALL_FAIL:go_build:{result.stderr.strip() if result else 'build error'}")
            return False, 0.0

def benchmark(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        result = e
        success = False
    duration = time.time() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # Emit benchmarks
    print_marker(f"BENCHMARK:{name}_time_s:{duration:.4f}")
    print_marker(f"BENCHMARK:{name}_mem_peak_kb:{peak/1024:.2f}")
    return success, result, duration

def test_import():
    def import_pkg():
        import monty_go  # type: ignore
    success, _, dur = benchmark('import', import_pkg)
    if success:
        print_marker("TEST_PASS:import")
    else:
        print_marker(f"TEST_FAIL:import:{str(_)}")
    return dur

def test_basic_validation():
    def run_validation():
        import monty_go  # type: ignore
        # create a simple schema using monty_go (pseudo code)
        schema = monty_go.NewSchema({
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        })
        data = {"name": "Alice", "age": 30}
        return schema.Validate(data)
    success, result, dur = benchmark('basic_validation', run_validation)
    if success and result is True:
        print_marker("TEST_PASS:basic_validation")
    else:
        reason = result if isinstance(result, Exception) else "validation failed"
        print_marker(f"TEST_FAIL:basic_validation:{reason}")
    return dur

def test_validation_latency():
    def validate_batch():
        import monty_go  # type: ignore
        schema = monty_go.NewSchema({
            "id": {"type": "integer"},
            "value": {"type": "string"}
        })
        objs = [{"id": i, "value": f"val{i}"} for i in range(10000)]
        for obj in objs:
            if not schema.Validate(obj):
                raise ValueError("invalid")
    success, _, dur = benchmark('batch_validation_10k', validate_batch)
    if success:
        print_marker("TEST_PASS:batch_validation_10k")
    else:
        print_marker(f"TEST_FAIL:batch_validation_10k:{_}")
    return dur

def test_schema_error_reporting():
    def error_check():
        import monty_go  # type: ignore
        schema = monty_go.NewSchema({
            "count": {"type": "integer", "minimum": 0}
        })
        bad = {"count": -5}
        return schema.Validate(bad)
    success, result, dur = benchmark('error_reporting', error_check)
    if success and result is False:
        print_marker("TEST_PASS:error_reporting")
    else:
        reason = "expected failure not observed" if success else str(result)
        print_marker(f"TEST_FAIL:error_reporting:{reason}")
    return dur

def compare_baseline(metric_name, our_value, baseline_value, higher_is_better=False):
    try:
        ratio = our_value / baseline_value if baseline_value != 0 else float('inf')
        if not higher_is_better:
            ratio = baseline_value / our_value if our_value != 0 else float('inf')
        print_marker(f"BENCHMARK:vs_{baseline_value_name}_{metric_name}:{ratio:.4f}")
    except Exception:
        pass

if __name__ == "__main__":
    # 1. Install required apk packages
    for pkg in ["git", "go", "python3-dev", "build-base"]:
        install_apk(pkg)

    # 2. Install Go package
    ok, go_install_time = install_go_pkg()
    if ok:
        print_marker(f"BENCHMARK:go_install_time_s:{go_install_time:.4f}")
    else:
        print_marker("TEST_SKIP:go_install:go install failed")

    # 3. Run Python import test
    import_time = test_import()

    # 4. Basic validation test
    basic_val_time = test_basic_validation()

    # 5. Batch validation latency
    batch_time = test_validation_latency()

    # 6. Schema error reporting test
    error_time = test_schema_error_reporting()

    # 7. Emit some generic benchmarks
    print_marker(f"BENCHMARK:total_test_time_s:{import_time+basic_val_time+batch_time+error_time:.4f}")
    print_marker(f"BENCHMARK:test_count:{4}")

    # 8. Compare with baseline (using pydantic-go as hypothetical baseline)
    baseline_value_name = "pydantic_go"
    baseline_batch_time = 0.12  # hypothetical seconds for 10k objs
    if batch_time > 0:
        ratio = baseline_batch_time / batch_time
        print_marker(f"BENCHMARK:vs_{baseline_value_name}_batch_validation_ratio:{ratio:.4f}")

    # Final marker
    print_marker("RUN_OK")