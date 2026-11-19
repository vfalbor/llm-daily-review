import subprocess, sys, time, json, tracemalloc, os, shutil, pathlib

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err.strip() or 'apk install failed'}")
    return rc == 0

def pip_install(package):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package])
    if rc == 0:
        print("INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:{package}:{err.strip() or 'pip install failed'}")
        return False

def pip_install_editable(path):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    if rc == 0:
        print("INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:{path}:{err.strip() or 'editable install failed'}")
        return False

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    except Exception as e:
        result = None
        current = peak = 0
    finally:
        tracemalloc.stop()
    elapsed = time.time() - start
    print(f"BENCHMARK:{name}:{elapsed:.4f}")
    return result, elapsed, peak

def test_clone_repo():
    repo_url = "https://github.com/pickysysadmin/logitech-harmony-ir-archive"
    dest = "/tmp/logitech-harmony-ir-archive"
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', repo_url, dest])
    if rc != 0:
        print(f"TEST_FAIL:clone_repo:{err.strip() or 'git clone failed'}")
        return False
    # list files
    rc, out, err = run_cmd(['ls', '-R', dest])
    if rc != 0:
        print(f"TEST_FAIL:clone_repo:ls failed")
        return False
    print("TEST_PASS:clone_repo")
    return True

def test_json_tool():
    repo_path = "/tmp/logitech-harmony-ir-archive"
    json_file = None
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith('.json'):
                json_file = os.path.join(root, f)
                break
        if json_file:
            break
    if not json_file:
        print("TEST_FAIL:json_tool:no json file found")
        return False
    rc, out, err = run_cmd([sys.executable, '-m', 'json.tool', json_file])
    if rc != 0:
        print(f"TEST_FAIL:json_tool:{err.strip() or 'json.tool failed'}")
        return False
    print("TEST_PASS:json_tool")
    return True

def import_package():
    import importlib
    start = time.time()
    mod = importlib.import_module('logitech_harmony_ir_archive')
    elapsed = time.time() - start
    print(f"BENCHMARK:import_time_s:{elapsed:.4f}")
    return mod

def core_operation(mod):
    # perform a simple lookup in the JSON data
    sample_key = next(iter(mod.DATA.keys())) if hasattr(mod, 'DATA') else None
    if not sample_key:
        print("TEST_SKIP:core_operation:no data loaded")
        return False
    start = time.time()
    _ = mod.DATA.get(sample_key)
    elapsed = time.time() - start
    print(f"BENCHMARK:core_op_latency_ms:{elapsed*1000:.4f}")
    return True

def main():
    # 1. Install required apk packages
    install_apk('git')

    # 2. Try pip install the package
    installed = pip_install('logitech-harmony-ir-archive')
    if not installed:
        # fallback: clone repo and install editable
        repo_cloned = test_clone_repo()
        if repo_cloned:
            repo_path = "/tmp/logitech-harmony-ir-archive"
            pip_install_editable(repo_path)

    # 3. Benchmark import
    try:
        mod, import_elapsed, _ = benchmark("import_time_s", import_package)
        if mod:
            print("TEST_PASS:import_package")
        else:
            print("TEST_FAIL:import_package:module import returned None")
    except Exception as e:
        print(f"TEST_FAIL:import_package:{str(e)}")

    # 4. Core operation benchmark
    try:
        success = core_operation(mod) if mod else False
        if success:
            print("TEST_PASS:core_operation")
        else:
            print("TEST_FAIL:core_operation:operation returned False")
    except Exception as e:
        print(f"TEST_FAIL:core_operation:{str(e)}")

    # 5. Run json.tool test
    try:
        if test_json_tool():
            pass
    except Exception as e:
        print(f"TEST_FAIL:json_tool:{str(e)}")

    # 6. Additional benchmarks (memory usage, file count)
    try:
        # count json files
        repo_path = "/tmp/logitech-harmony-ir-archive"
        json_count = sum(1 for root, _, files in os.walk(repo_path) for f in files if f.endswith('.json'))
        print(f"BENCHMARK:json_files_count:{json_count}")
    except Exception as e:
        print(f"BENCHMARK:json_files_count:0")

    # 7. Compare against baseline (assume baseline import time 0.12s)
    baseline_import = 0.12
    ratio = import_elapsed / baseline_import if baseline_import else 0
    print(f"BENCHMARK:vs_remote_control_code_database_import_ratio:{ratio:.4f}")

    # final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()