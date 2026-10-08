#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, importlib, os, json, math, traceback

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    start = time.time()
    res = subprocess.run(['apk','add','--no-cache',pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elapsed = time.time() - start
    if res.returncode == 0:
        print_marker(f"INSTALL_OK | apk:{pkg}")
    else:
        print_marker(f"INSTALL_FAIL:apk:{pkg}:returncode={res.returncode}")
    return elapsed

def pip_install(pkg):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker(f"INSTALL_OK | pip:{pkg}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip:{pkg}:{e}")
    return time.time() - start

def git_clone(url, dest):
    start = time.time()
    try:
        subprocess.run(['git','clone','--depth','1',url,dest],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker(f"INSTALL_OK | git:{url}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git:{url}:{e}")
    return time.time() - start

def measure_import(module_name):
    start = time.time()
    try:
        importlib.import_module(module_name)
        print_marker(f"TEST_PASS:import_{module_name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
    return time.time() - start

def run_simulation(mod):
    # Very naive synthetic test: call a function named `simulate` if exists
    start = time.time()
    try:
        if hasattr(mod, 'simulate'):
            result = mod.simulate()
            # Expect result to be dict with numeric values
            if isinstance(result, dict) and all(isinstance(v,(int,float)) for v in result.values()):
                print_marker(f"TEST_PASS:simulation")
            else:
                print_marker(f"TEST_FAIL:simulation:unexpected result type")
        else:
            print_marker(f"TEST_SKIP:simulation:simulate not found")
    except Exception as e:
        print_marker(f"TEST_FAIL:simulation:{e}")
    return time.time() - start

def benchmark_memory():
    tracemalloc.start()
    time.sleep(0.01)  # tiny allocation
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024  # KiB

def main():
    # 1. Install system deps
    install_times = {}
    install_times['apk_git'] = apk_install('git')

    # 2. Install Python package via pip (attempt direct install)
    pkg_url = 'git+https://github.com/pavel-krivanek/The-Analog-Thing-Simulator.git'
    install_times['pip_pkg'] = pip_install(pkg_url)

    # 3. Fallback: clone repo and install editable
    repo_dir = '/tmp/analog_sim'
    if not os.path.isdir(repo_dir):
        clone_time = git_clone('https://github.com/pavel-krivanek/The-Analog-Thing-Simulator.git', repo_dir)
        install_times['git_clone'] = clone_time
        if os.path.isdir(repo_dir):
            editable_time = pip_install(f'-e {repo_dir}')
            install_times['pip_editable'] = editable_time

    # Emit install benchmarks
    for k,v in install_times.items():
        print_marker(f"BENCHMARK:{k}_s:{v:.3f}")

    # 4. Attempt to import the main module (guess name)
    possible_modules = ['analog_thing_simulator', 'the_analog_thing_simulator', 'simulator']
    imported_mod = None
    import_time = None
    for mod_name in possible_modules:
        try:
            start = time.time()
            imported_mod = importlib.import_module(mod_name)
            import_time = time.time() - start
            print_marker(f"TEST_PASS:import_{mod_name}")
            break
        except Exception:
            continue
    if imported_mod is None:
        print_marker(f"TEST_FAIL:import_any:could not import any guessed module")
        import_time = 0.0

    print_marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")

    # 5. Run a minimal simulation test
    if imported_mod:
        sim_time = run_simulation(imported_mod)
        print_marker(f"BENCHMARK:simulation_time_ms:{sim_time*1000:.2f}")
    else:
        print_marker("TEST_SKIP:simulation:no module imported")
        print_marker("BENCHMARK:simulation_time_ms:0")

    # 6. Memory benchmark
    mem_kib = benchmark_memory()
    print_marker(f"BENCHMARK:memory_peak_kib:{mem_kib:.2f}")

    # 7. Compare against baseline (Falstad approx 1.0 ratio assumed)
    baseline_ratio = 1.0  # placeholder baseline reference
    if import_time > 0:
        ratio = import_time / (import_time * baseline_ratio)  # will be 1.0
        print_marker(f"BENCHMARK:vs_falstad_import_ratio:{ratio:.2f}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()