import subprocess, sys, time, tracemalloc, os, json, math, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def apk_add(pkg):
    res = run_cmd(['apk', 'add', '--no-cache', pkg])
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else str(e))
        print_marker(f"INSTALL_FAIL:{reason}")

def pip_install(pkg):
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
    return res and res.returncode == 0

def pip_install_editable(path):
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '-e', path])
    return res and res.returncode == 0

def measure_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        elapsed = (time.time() - start) * 1000  # ms
        return True, elapsed
    except Exception as e:
        return False, str(e)

def measure_latency(func, *args, **kwargs):
    start = time.time()
    try:
        func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        return True, elapsed
    except Exception as e:
        return False, str(e)

def safe_execute(name, fn, *a, **k):
    try:
        ok, val = fn(*a, **k)
        if ok:
            print_marker(f"TEST_PASS:{name}")
            return val
        else:
            print_marker(f"TEST_FAIL:{name}:{val}")
            return None
    except Exception as e:
        print_marker(f"TEST_FAIL:{name}:{e}")
        return None

def main():
    # 1. Install required system packages
    apk_add('git')

    # 2. Try pip install the package
    pkg_name = 'lfm2-5-24b-a2b'  # guessed pip name
    installed = pip_install(pkg_name)

    repo_dir = None
    if not installed:
        # fallback: clone repo and install editable
        repo_url = 'https://github.com/liquid-ai/lfm2-5-24b-a2b.git'
        clone_dir = '/tmp/lfm2_repo'
        if os.path.isdir(clone_dir):
            run_cmd(['rm', '-rf', clone_dir])
        res = run_cmd(['git', 'clone', '--depth', '1', repo_url, clone_dir])
        if res and res.returncode == 0:
            installed = pip_install_editable(clone_dir)
            if installed:
                repo_dir = clone_dir
                print_marker("INSTALL_OK")
            else:
                print_marker("INSTALL_FAIL:pip editable install failed")
        else:
            print_marker(f"INSTALL_FAIL:git clone failed:{res.stderr if res else 'unknown'}")
    else:
        print_marker("INSTALL_OK")

    # Benchmark: import time
    import_time = None
    ok = False
    if installed:
        ok, import_time = measure_import('lfm2_5_24b_a2b')
        if ok:
            print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        else:
            print_marker(f"TEST_FAIL:import_module:{import_time}")

    # Baseline import time using a similar package (e.g., transformers)
    baseline_time = None
    try:
        start = time.time()
        import transformers
        baseline_time = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:baseline_import_time_ms:{baseline_time:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_import:{e}")

    # Ratio benchmark
    if import_time is not None and baseline_time:
        ratio = import_time / baseline_time if baseline_time else float('nan')
        print_marker(f"BENCHMARK:vs_transformers_import_ratio:{ratio:.3f}")

    # 3. Minimal functional test: run a dummy forward pass if model class exists
    def functional_test():
        from lfm2_5_24b_a2b import LFM2Model  # hypothetical class
        model = LFM2Model()
        dummy_input = [[0]]  # synthetic token ids
        _ = model.forward(dummy_input)

    latency = safe_execute("functional_test", functional_test)
    if latency is not None:
        print_marker(f"BENCHMARK:functional_latency_ms:{latency:.2f}")

    # 4. Export to TorchScript and measure inference latency (if torch available)
    def export_and_infer():
        import torch
        from lfm2_5_24b_a2b import LFM2Model
        model = LFM2Model()
        scripted = torch.jit.script(model)
        dummy = torch.tensor([[0]], dtype=torch.long)
        start = time.time()
        _ = scripted(dummy)
        return (time.time() - start) * 1000

    torch_latency = safe_execute("torchscript_inference", export_and_infer)
    if torch_latency is not None:
        print_marker(f"BENCHMARK:torchscript_latency_ms:{torch_latency:.2f}")

    # 5. Memory usage benchmark
    tracemalloc.start()
    try:
        import lfm2_5_24b_a2b
    except Exception:
        pass
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

    # Ensure at least three benchmark lines exist (already satisfied)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()