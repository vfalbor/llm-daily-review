#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json, math

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)

def print_marker(msg):
    print(msg, flush=True)

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def test_result(status, name, reason=""):
    if status == "PASS":
        print_marker(f"TEST_PASS:{name}")
    elif status == "FAIL":
        print_marker(f"TEST_FAIL:{name}:{reason}")
    elif status == "SKIP":
        print_marker(f"TEST_SKIP:{name}:{reason}")

def install_apk_packages():
    start = time.time()
    ok, err = run_cmd(['apk','add','--no-cache','git'])
    if ok:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err}")
    benchmark("apk_install_time_s", f"{time.time()-start:.3f}")

def pip_install(package):
    start = time.time()
    ok, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package])
    benchmark("pip_install_time_s", f"{time.time()-start:.3f}")
    return ok, err

def git_clone(repo, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    start = time.time()
    ok, err = run_cmd(['git','clone',repo,dest])
    benchmark("git_clone_time_s", f"{time.time()-start:.3f}")
    return ok, err

def pip_install_editable(path):
    start = time.time()
    ok, err = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
    benchmark("pip_editable_install_time_s", f"{time.time()-start:.3f}")
    return ok, err

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        import_time = (time.time()-start)*1000
        current, peak = tracemalloc.get_traced_memory()
        benchmark("import_time_ms", f"{import_time:.2f}")
        benchmark("import_mem_peak_kb", f"{peak/1024:.2f}")
        return True, ""
    except Exception as e:
        return False, str(e)
    finally:
        tracemalloc.stop()

def functional_test_pgp():
    try:
        import pgp
    except Exception as e:
        return False, f"import error: {e}"
    # simple symmetric encrypt/decrypt using a passphrase
    data = b"Hello World"
    passphrase = "testpass"
    try:
        enc = pgp.encrypt(data, passphrase=passphrase)
        dec = pgp.decrypt(enc, passphrase=passphrase)
        if dec != data:
            return False, "decrypted data mismatch"
        return True, ""
    except Exception as e:
        return False, f"operation error: {e}"

def functional_test_gnupg():
    try:
        import gnupg
    except Exception as e:
        return False, f"gnupg import error: {e}"
    gpg = gnupg.GPG()
    data = b"Hello World"
    passphrase = "testpass"
    try:
        enc = gpg.encrypt(data, recipients=None, symmetric='AES256', passphrase=passphrase, always_trust=True)
        if not enc.ok:
            return False, f"gpg encrypt fail: {enc.status}"
        dec = gpg.decrypt(enc.data, passphrase=passphrase)
        if not dec.ok or dec.data != data:
            return False, "gpg decrypt mismatch"
        return True, ""
    except Exception as e:
        return False, f"gpg operation error: {e}"

def compare_benchmarks(pgp_latency, gnupg_latency):
    if gnupg_latency == 0:
        ratio = "inf"
    else:
        ratio = f"{pgp_latency/gnupg_latency:.3f}"
    benchmark("vs_gnupg_latency_ratio", ratio)

def main():
    # 1. Install system deps
    install_apk_packages()

    # 2. Install pgp via pip (git+https)
    pgp_installed = False
    ok, err = pip_install('git+https://github.com/philzimmermann/PGP')
    if ok:
        pgp_installed = True
    else:
        # fallback: clone and install editable
        okc, errc = git_clone('https://github.com/philzimmermann/PGP.git', '/tmp/PGP')
        if okc:
            ok, err = pip_install_editable('/tmp/PGP')
            pgp_installed = ok

    if not pgp_installed:
        test_result("SKIP", "pgp_install", "could not install pgp package")
    else:
        test_result("PASS", "pgp_install")

    # 3. Measure import time
    imp_ok, imp_err = measure_import('pgp')
    if imp_ok:
        test_result("PASS", "pgp_import")
    else:
        test_result("FAIL", "pgp_import", imp_err)

    # 4. Functional test and latency benchmark
    start = time.time()
    func_ok, func_err = functional_test_pgp()
    latency_ms = (time.time()-start)*1000
    benchmark("pgp_operation_latency_ms", f"{latency_ms:.2f}")
    if func_ok:
        test_result("PASS", "pgp_functional")
    else:
        test_result("FAIL", "pgp_functional", func_err)

    # 5. Install baseline gnupg python wrapper
    ok, err = pip_install('python-gnupg')
    if not ok:
        test_result("SKIP", "gnupg_install", "failed to install python-gnupg")
    else:
        test_result("PASS", "gnupg_install")

    # 6. Measure gnupg import
    imp_ok_g, imp_err_g = measure_import('gnupg')
    if imp_ok_g:
        test_result("PASS", "gnupg_import")
    else:
        test_result("FAIL", "gnupg_import", imp_err_g)

    # 7. Functional test for gnupg
    start = time.time()
    func_ok_g, func_err_g = functional_test_gnupg()
    gnupg_latency_ms = (time.time()-start)*1000
    benchmark("gnupg_operation_latency_ms", f"{gnupg_latency_ms:.2f}")
    if func_ok_g:
        test_result("PASS", "gnupg_functional")
    else:
        test_result("FAIL", "gnupg_functional", func_err_g)

    # 8. Compare benchmarks
    if func_ok and func_ok_g:
        compare_benchmarks(latency_ms, gnupg_latency_ms)

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()