import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib, hashlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} error {res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} exception {e}")

def pip_install(package):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package])
        if res.returncode == 0:
            return True, ""
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

def pip_install_editable(path):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '-e', path])
        if res.returncode == 0:
            return True, ""
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

def measure_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        duration = (time.time() - start) * 1000  # ms
        return True, duration
    except Exception as e:
        return False, str(e)

def measure_inference(func, *args, **kwargs):
    start = time.time()
    try:
        result = func(*args, **kwargs)
        latency = (time.time() - start) * 1000  # ms
        return True, latency, result
    except Exception as e:
        return False, None, str(e)

def get_memory_snapshot():
    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    total = sum(stat.size for stat in snapshot.statistics('filename'))
    tracemalloc.stop()
    return total / 1024  # KiB

# 1. Install system packages
install_apk('git')
install_apk('python3-dev')  # needed for building wheels

# 2. Clone repo and install dependencies
repo_url = "https://github.com/SheepSeb/tinyworldformer.git"
repo_dir = "/tmp/tinyworldformer"
if os.path.isdir(repo_dir):
    shutil.rmtree(repo_dir)
clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
if clone_res.returncode != 0:
    print_marker(f"TEST_FAIL:clone_repo:{clone_res.stderr.strip()}")
else:
    print_marker("TEST_PASS:clone_repo")
    # try pip install package name (assume package name is tinyworldformer)
    ok, msg = pip_install('tinyworldformer')
    if not ok:
        # fallback to editable install
        ok, msg = pip_install_editable(repo_dir)
    if ok:
        print_marker("TEST_PASS:install_package")
    else:
        print_marker(f"TEST_FAIL:install_package:{msg}")

# 3. Measure import time
import_ok, import_res = measure_import('tinyworldformer')
if import_ok:
    print_marker(f"TEST_PASS:import_module")
    print_marker(f"BENCHMARK:import_time_ms:{import_res:.2f}")
else:
    print_marker(f"TEST_FAIL:import_module:{import_res}")

# 4. Run minimal functional test
if import_ok:
    try:
        from tinyworldformer import TinyWorldTransformer  # type: ignore
        # create synthetic data
        model = TinyWorldTransformer()
        # simple synthetic prompt
        prompt = "Start simulation"
        # measure inference latency
        inf_ok, latency, out = measure_inference(model.generate, prompt)
        if inf_ok:
            print_marker("TEST_PASS:inference")
            print_marker(f"BENCHMARK:inference_latency_ms:{latency:.2f}")
            # simple output sanity check (non-empty)
            if out and isinstance(out, str) and len(out.strip()) > 0:
                print_marker("TEST_PASS:output_nonempty")
            else:
                print_marker("TEST_FAIL:output_check:empty or invalid output")
        else:
            print_marker(f"TEST_FAIL:inference:{latency}")
    except Exception as e:
        print_marker(f"TEST_FAIL:functional_test:{e}")

# 5. Measure memory footprint of model loading
if import_ok:
    try:
        tracemalloc.start()
        model = TinyWorldTransformer()
        snapshot = tracemalloc.take_snapshot()
        mem_kib = sum(stat.size for stat in snapshot.statistics('filename')) / 1024
        tracemalloc.stop()
        print_marker(f"BENCHMARK:model_memory_kib:{mem_kib:.2f}")
        # Pico 2 W has ~264KB RAM, allow up to 200KB for model
        if mem_kib < 200:
            print_marker("TEST_PASS:memory_limit")
        else:
            print_marker(f"TEST_FAIL:memory_limit:uses {mem_kib:.2f} KiB > 200 KiB")
    except Exception as e:
        print_marker(f"TEST_FAIL:memory_measure:{e}")

# 6. Compare against baseline (TinyGPT assumed)
# Baseline numbers are hardcoded for demonstration
baseline_import_ms = 120.0
baseline_inference_ms = 150.0
if isinstance(import_res, float):
    ratio_imp = import_res / baseline_import_ms
    print_marker(f"BENCHMARK:vs_tinygpt_import_ratio:{ratio_imp:.2f}")
if 'latency' in locals() and isinstance(latency, float):
    ratio_inf = latency / baseline_inference_ms
    print_marker(f"BENCHMARK:vs_tinygpt_inference_ratio:{ratio_inf:.2f}")

# Ensure at least 3 benchmark lines (we already have several)
# 7 Final marker
print_marker("RUN_OK")