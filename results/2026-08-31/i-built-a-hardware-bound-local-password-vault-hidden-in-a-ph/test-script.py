import subprocess, sys, time, tracemalloc, os, json, shutil, pathlib, statistics

def print_marker(msg):
    print(msg, flush=True)

def run_apk_install(pkg):
    try:
        start = time.time()
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:apk_install_{pkg}_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk_{pkg}:{e}")

def pip_install(package):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', package], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:pip_install_{package}_s:{elapsed:.3f}")
        print_marker("INSTALL_OK")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip_{package}:{e}")
        return False

def git_clone(url, dest):
    try:
        start = time.time()
        subprocess.run(['git', 'clone', '--depth', '1', url, dest], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:git_clone_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git_clone:{e}")
        return False

def import_module_timed(name):
    try:
        start = time.time()
        mod = __import__(name)
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:import_{name}_ms:{elapsed:.2f}")
        return mod
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{name}:{e}")
        return None

def benchmark(name, func, *args, **kwargs):
    try:
        tracemalloc.start()
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:{name}_ms:{elapsed:.2f}")
        print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.2f}")
        return result
    except Exception as e:
        print_marker(f"TEST_FAIL:{name}:{e}")
        return None

# 1. Install system dependencies
run_apk_install('git')
run_apk_install('python3')  # ensure python present (already in base)

# 2. Install blindlock via pip, fallback to git+editable
package_name = 'blindlock'
installed = pip_install(package_name)
if not installed:
    repo_url = 'https://github.com/BlindLock/blindlock.git'
    clone_dir = '/tmp/blindlock_src'
    if os.path.isdir(clone_dir):
        shutil.rmtree(clone_dir)
    if git_clone(repo_url, clone_dir):
        try:
            start = time.time()
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', '.'],
                           cwd=clone_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elapsed = time.time() - start
            print_marker(f"BENCHMARK:pip_editable_install_s:{elapsed:.3f}")
            print_marker("INSTALL_OK")
            installed = True
        except Exception as e:
            print_marker(f"INSTALL_FAIL:pip_editable:{e}")

# 3. Import module
blindlock = import_module_timed('blindlock')
if not blindlock:
    # cannot continue functional tests without module
    print_marker("RUN_OK")
    sys.exit(0)

# Helper functions for tests
def test_create_vault():
    try:
        vault = blindlock.Vault()
        return vault
    except Exception as e:
        raise RuntimeError(f"Vault creation failed: {e}")

def test_add_password(vault):
    try:
        vault.add('example.com', 'user', 's3cr3t')
        return True
    except Exception as e:
        raise RuntimeError(f"Add password failed: {e}")

def test_export_image(vault, path):
    try:
        vault.export_image(path)
        return os.path.isfile(path)
    except Exception as e:
        raise RuntimeError(f"Export image failed: {e}")

def test_import_image(path):
    try:
        imported = blindlock.Vault.from_image(path)
        return imported
    except Exception as e:
        raise RuntimeError(f"Import image failed: {e}")

def test_verify(vault, imported):
    try:
        pw = imported.get('example.com', 'user')
        return pw == 's3cr3t'
    except Exception as e:
        raise RuntimeError(f"Verification failed: {e}")

# 4. Run functional tests with benchmarking
vault = benchmark("create_vault", test_create_vault)
if vault is None:
    print_marker("RUN_OK")
    sys.exit(0)

if benchmark("add_password", test_add_password, vault):
    print_marker("TEST_PASS:add_password")
else:
    print_marker("TEST_FAIL:add_password:unknown")

img_path = '/tmp/vault_image.jpg'
export_success = benchmark("export_image", test_export_image, vault, img_path)
if export_success:
    print_marker("TEST_PASS:export_image")
else:
    print_marker("TEST_FAIL:export_image:export_failed")

imported_vault = benchmark("import_image", test_import_image, img_path)
if imported_vault:
    print_marker("TEST_PASS:import_image")
else:
    print_marker("TEST_FAIL:import_image:import_failed")

if imported_vault:
    if benchmark("verify_password", test_verify, vault, imported_vault):
        print_marker("TEST_PASS:verify_password")
    else:
        print_marker("TEST_FAIL:verify_password:mismatch")

# 5. Measure encryption/decryption latency directly
def measure_encrypt_decrypt(vault):
    start = time.time()
    token = vault.encrypt('sample data')
    dec = vault.decrypt(token)
    if dec != 'sample data':
        raise RuntimeError("Roundtrip mismatch")
    return (time.time() - start) * 1000

enc_time = benchmark("encrypt_decrypt_latency", measure_encrypt_decrypt, vault)

# 6. Baseline comparison against KeePass (using keepassxc-cli if installed)
baseline_installed = shutil.which('keepassxc-cli') is not None
if baseline_installed:
    # simple benchmark: generate a dummy keepass db and measure open time
    dummy_db = '/tmp/dummy.kdbx'
    try:
        subprocess.run(['keepassxc-cli', 'create', '-p', 'test', dummy_db],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start = time.time()
        subprocess.run(['keepassxc-cli', 'open', '-p', 'test', dummy_db],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        keepass_time = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:keepass_open_ms:{keepass_time:.2f}")
        if enc_time:
            ratio = enc_time / keepass_time if keepass_time else 0
            print_marker(f"BENCHMARK:vs_keepass_encrypt_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:keepass_baseline:{e}")

# Ensure at least 3 benchmark lines (already emitted many)
print_marker("RUN_OK")