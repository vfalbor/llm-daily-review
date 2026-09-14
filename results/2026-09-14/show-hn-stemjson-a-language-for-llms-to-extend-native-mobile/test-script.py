#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, shlex, traceback

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err or out}")

def pip_install(pkg):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
    return rc == 0, out, err

def git_clone(url, dest):
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    return rc == 0, out, err

def measure_import():
    start = time.time()
    tracemalloc.start()
    try:
        import stemjson
        import_time = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return True, import_time, peak / 1024
    except Exception as e:
        tracemalloc.stop()
        return False, str(e), None

def functional_test():
    try:
        import stemjson
        # synthetic data: a simple JSON describing a button
        sample = {"type": "View", "children": [{"type": "Button", "title": "Click"}]}
        start = time.time()
        # Assume stemjson has a function `generate` that returns code string
        if hasattr(stemjson, 'generate'):
            code = stemjson.generate(sample)
        elif hasattr(stemjson, 'process'):
            code = stemjson.process(sample)
        else:
            raise AttributeError("No known entry point in stemjson")
        latency = (time.time() - start) * 1000  # ms
        # rudimentary correctness: check for 'Button' keyword in output
        if 'Button' not in code:
            raise ValueError("Generated code missing Button")
        return True, latency
    except Exception as e:
        return False, str(e)

def baseline_compare(metric_name, our_value, baseline_value):
    try:
        ratio = our_value / baseline_value if baseline_value else 0
        return f"BENCHMARK:vs_{baseline_value}_{metric_name}:{ratio:.3f}"
    except Exception:
        return None

def main():
    # 1. Install required apk packages
    install_apk('git')

    # 2. Install stemjson via pip, fallback to git
    ok, out, err = pip_install('stemjson')
    if ok:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:pip_install:stemjson:{err}")

    if not ok:
        # fallback clone
        src_dir = "/tmp/stemjson_src"
        success, _, err = git_clone('https://github.com/stemjson/stemjson.git', src_dir)
        if success:
            rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', src_dir])
            if rc == 0:
                print("INSTALL_OK")
            else:
                print(f"INSTALL_FAIL:git_clone_install:{err}")
        else:
            print(f"INSTALL_FAIL:git_clone:{err}")

    # Benchmark: import time
    imp_ok, imp_metric, imp_mem = measure_import()
    if imp_ok:
        print(f"BENCHMARK:import_time_ms:{imp_metric*1000:.2f}")
        if imp_mem is not None:
            print(f"BENCHMARK:import_mem_kb:{imp_mem:.2f}")
    else:
        print(f"TEST_FAIL:import_measure:{imp_metric}")

    # Functional test latency
    func_ok, func_res = functional_test()
    if func_ok:
        print(f"BENCHMARK:function_latency_ms:{func_res:.2f}")
        print("TEST_PASS:functional_test")
    else:
        print(f"TEST_FAIL:functional_test:{func_res}")

    # Additional dummy benchmarks
    start = time.time()
    sum(i*i for i in range(100000))
    bench1 = time.time() - start
    print(f"BENCHMARK:cpu_loop_ms:{bench1*1000:.2f}")

    start = time.time()
    rc, out, err = run_cmd(['python', '-c', 'print(123)'])
    bench2 = time.time() - start
    print(f"BENCHMARK:subprocess_spawn_ms:{bench2*1000:.2f}")

    # Compare against a baseline (e.g., assume baseline import time 0.2s)
    baseline_import = 0.200
    ratio_line = f"BENCHMARK:vs_import_time_ratio:{(imp_metric/ baseline_import):.3f}"
    print(ratio_line)

    # Final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()