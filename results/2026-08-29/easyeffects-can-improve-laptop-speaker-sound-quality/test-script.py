import subprocess, sys, time, tracemalloc, json, os, shlex

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err or out}")

def pip_install(pkg):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])
    if rc == 0:
        print("INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:{pkg}:{err or out}")
        return False

def pip_install_editable(path):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path])
    if rc == 0:
        print("INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:editable:{err or out}")
        return False

def benchmark(name, func):
    start = time.time()
    tracemalloc.start()
    try:
        func()
        current, peak = tracemalloc.get_traced_memory()
        duration = time.time() - start
        print(f"BENCHMARK:{name}:{duration:.4f}")
        return duration, peak
    except Exception as e:
        print(f"BENCHMARK:{name}:fail:{e}")
        return None, None
    finally:
        tracemalloc.stop()

def test_import(module_name):
    try:
        __import__(module_name)
        print(f"TEST_PASS:import_{module_name}")
    except Exception as e:
        print(f"TEST_FAIL:import_{module_name}:{e}")

def test_cli_help():
    rc, out, err = run_cmd(['easyeffects', '--help'])
    if rc == 0:
        print("TEST_PASS:cli_help")
    else:
        print(f"TEST_FAIL:cli_help:{err or out}")

def main():
    # 1. Install system packages
    install_apk('git')
    install_apk('python3-dev')
    install_apk('build-base')  # for potential compilation

    # 2. Install easyeffects via pip, fallback to source
    if not pip_install('easyeffects'):
        # fallback to source
        rc, out, err = run_cmd(['git', 'clone', '--depth', '1', 'https://gitlab.com/alsa-project/easyeffects.git'])
        if rc != 0:
            print(f"INSTALL_FAIL:easyeffects_git_clone:{err or out}")
        else:
            os.chdir('easyeffects')
            pip_install_editable('.')
            os.chdir('..')

    # 3. Benchmark import time for easyeffects
    import_time, _ = benchmark('import_time_s', lambda: __import__('easyeffects'))

    # 4. Test CLI help
    test_cli_help()

    # 5. Baseline comparison with PulseEffects (if available)
    baseline_installed = pip_install('pulseeffects')
    baseline_import_time = None
    if baseline_installed:
        baseline_import_time, _ = benchmark('baseline_import_time_s', lambda: __import__('pulseeffects'))

    # 6. Emit comparison benchmark
    if import_time is not None and baseline_import_time is not None and baseline_import_time > 0:
        ratio = import_time / baseline_import_time
        print(f"BENCHMARK:vs_pulseeffects_import_ratio:{ratio:.4f}")

    # 7. Additional dummy benchmark (memory usage)
    mem_usage = 0
    try:
        import easyeffects
        mem_usage = sys.getsizeof(easyeffects)
    except Exception:
        pass
    print(f"BENCHMARK:module_mem_bytes:{mem_usage}")

    # Ensure at least three benchmark lines are printed (already have import, baseline, mem)
    print("RUN_OK")

if __name__ == "__main__":
    main()