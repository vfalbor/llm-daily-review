import subprocess, sys, time, tracemalloc, os, shutil, json, hashlib

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk(pkgs):
    start = time.time()
    res = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print(f"INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else "exception")
        print(f"INSTALL_FAIL:{reason}")
    print(f"BENCHMARK:apk_install_time_s:{elapsed:.3f}")

def pip_install(package):
    start = time.time()
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print(f"INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else "exception")
        print(f"INSTALL_FAIL:{reason}")
    print(f"BENCHMARK:pip_install_time_s:{elapsed:.3f}")
    return res and res.returncode == 0

def git_clone(repo, dest):
    start = time.time()
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    elapsed = time.time() - start
    if res and res.returncode == 0:
        print(f"INSTALL_OK")
    else:
        reason = (res.stderr.strip() if res else "exception")
        print(f"INSTALL_FAIL:{reason}")
    print(f"BENCHMARK:git_clone_time_s:{elapsed:.3f}")
    return res and res.returncode == 0

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        import_time = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"TEST_PASS:import_{module_name}")
        print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
        print(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
    except Exception as e:
        tracemalloc.stop()
        print(f"TEST_FAIL:import_{module_name}:{e}")

def functional_test():
    start = time.time()
    try:
        from luciole_mono import render_sample  # hypothetical API
        sample = "def hello():\n    print('Hello, world!')"
        out = render_sample(sample)
        if isinstance(out, str) and "Hello" in out:
            print("TEST_PASS:functional_render")
        else:
            print("TEST_FAIL:functional_render:unexpected output")
    except Exception as e:
        print(f"TEST_FAIL:functional_render:{e}")
    finally:
        elapsed = time.time() - start
        print(f"BENCHMARK:functional_render_ms:{elapsed*1000:.2f}")

def baseline_compare():
    # Simple baseline using JetBrains Mono via pip package (hypothetical)
    start = time.time()
    try:
        from jetbrains_mono import render_sample as baseline_render
        from luciole_mono import render_sample as luciole_render
        sample = "x = 1\nwhile x < 10:\n    x += 1"
        t0 = time.time()
        baseline_render(sample)
        t1 = time.time()
        luciole_render(sample)
        t2 = time.time()
        ratio = (t2 - t1) / (t1 - t0) if (t1 - t0) != 0 else 0
        print(f"BENCHMARK:vs_jetbrains_mono_ratio:{ratio:.3f}")
    except Exception as e:
        print(f"TEST_FAIL:baseline_compare:{e}")
    finally:
        print(f"BENCHMARK:baseline_compare_total_ms:{(time.time()-start)*1000:.2f}")

def main():
    # 1. Install system deps
    install_apk(['git', 'python3-dev', 'build-base'])  # build-base for potential npm builds

    # 2. Try pip install
    installed = pip_install('luciole-mono')
    if not installed:
        # fallback to git clone + pip install -e
        repo = "https://github.com/scriptor-pro/luciole-mono.git"
        dest = "/tmp/luciole-mono"
        if git_clone(repo, dest):
            res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', dest])
            if res and res.returncode == 0:
                print("INSTALL_OK")
            else:
                reason = res.stderr.strip() if res else "exception"
                print(f"INSTALL_FAIL:{reason}")

    # 3. Measure import
    measure_import('luciole_mono')

    # 4. Functional test
    functional_test()

    # 5. Baseline comparison
    baseline_compare()

    # 6. Additional benchmarks (file size)
    try:
        import importlib.util, pathlib
        spec = importlib.util.find_spec('luciole_mono')
        if spec and spec.origin:
            size = pathlib.Path(spec.origin).stat().st_size
            print(f"BENCHMARK:luciole_mono_pkg_size_bytes:{size}")
        else:
            print("TEST_FAIL:file_size:module not found")
    except Exception as e:
        print(f"TEST_FAIL:file_size:{e}")

    print("RUN_OK")

if __name__ == "__main__":
    main()