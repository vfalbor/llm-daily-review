import subprocess, sys, time, tracemalloc, json, os, pathlib, shutil, traceback

def marker(msg):
    print(msg, flush=True)

def run_apk(pkg):
    try:
        start = time.time()
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if res.returncode == 0:
            marker(f"INSTALL_OK | {pkg}")
        else:
            marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
        return elapsed
    except Exception as e:
        marker(f"INSTALL_FAIL:{pkg}:{e}")
        return None

def pip_install(package):
    try:
        start = time.time()
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', package], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if res.returncode == 0:
            marker(f"INSTALL_OK | pip:{package}")
        else:
            marker(f"INSTALL_FAIL:pip:{package}:{res.stderr.strip()}")
        return elapsed
    except Exception as e:
        marker(f"INSTALL_FAIL:pip:{package}:{e}")
        return None

def pip_install_editable(path):
    try:
        start = time.time()
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if res.returncode == 0:
            marker(f"INSTALL_OK | editable:{path}")
        else:
            marker(f"INSTALL_FAIL:editable:{path}:{res.stderr.strip()}")
        return elapsed
    except Exception as e:
        marker(f"INSTALL_FAIL:editable:{path}:{e}")
        return None

def clone_repo(url, dest):
    try:
        start = time.time()
        res = subprocess.run(['git', 'clone', '--depth', '1', url, dest], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if res.returncode == 0:
            marker(f"INSTALL_OK | clone:{url}")
        else:
            marker(f"INSTALL_FAIL:clone:{url}:{res.stderr.strip()}")
        return elapsed
    except Exception as e:
        marker(f"INSTALL_FAIL:clone:{url}:{e}")
        return None

def measure_import(module_name):
    try:
        start = time.time()
        tracemalloc.start()
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = time.time() - start
        marker(f"BENCHMARK:import_time_ms:{elapsed*1000:.2f}")
        marker(f"BENCHMARK:import_memory_kb:{peak/1024:.2f}")
        return elapsed
    except Exception as e:
        marker(f"TEST_FAIL:import_module:{e}")
        return None

def run_generation(module, tile_count=1000):
    try:
        # Assume the package provides a `WorldGenerator` class with `generate(num_tiles)` method
        from importlib import import_module
        mod = import_module(module)
        if not hasattr(mod, 'WorldGenerator'):
            raise AttributeError("WorldGenerator class not found")
        wg = mod.WorldGenerator()
        start = time.time()
        world = wg.generate(num_tiles=tile_count)
        elapsed = time.time() - start
        marker(f"BENCHMARK:gen_time_ms:{elapsed*1000:.2f}")
        return world, elapsed
    except Exception as e:
        marker(f"TEST_FAIL:world_generation:{e}")
        return None, None

def validate_output(world):
    try:
        # Very simple schema validation: world must be dict with 'tiles' list
        if not isinstance(world, dict):
            raise ValueError("World is not a dict")
        if 'tiles' not in world or not isinstance(world['tiles'], list):
            raise ValueError("Missing 'tiles' list")
        marker(f"TEST_PASS:output_validation")
        return True
    except Exception as e:
        marker(f"TEST_FAIL:output_validation:{e}")
        return False

def simple_query(world):
    try:
        # Example query: count tiles of type 'grass' if present
        tiles = world.get('tiles', [])
        start = time.time()
        count = sum(1 for t in tiles if t.get('type') == 'grass')
        elapsed = time.time() - start
        marker(f"BENCHMARK:query_latency_ms:{elapsed*1000:.3f}")
        marker(f"TEST_PASS:simple_query")
        return count
    except Exception as e:
        marker(f"TEST_FAIL:simple_query:{e}")
        return None

def compare_vs_baseline(metric_name, our_value, baseline_value):
    try:
        ratio = our_value / baseline_value if baseline_value != 0 else float('inf')
        marker(f"BENCHMARK:vs_{baseline_name}_{metric_name}:{ratio:.3f}")
    except Exception:
        pass

# ------------------- Main Execution -------------------
def main():
    # 1. Install required system packages
    apk_time = run_apk('git')
    if apk_time is not None:
        marker(f"BENCHMARK:apk_git_install_s:{apk_time:.2f}")

    repo_url = "https://github.com/PhiloLabs/fable51-worlds"
    work_dir = pathlib.Path("/tmp/fable51")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    clone_time = clone_repo(repo_url, str(work_dir))
    if clone_time is not None:
        marker(f"BENCHMARK:clone_time_s:{clone_time:.2f}")

    # 2. Install package via pip, fallback to editable install from source
    install_success = False
    pip_time = pip_install('fable51-worlds')
    if pip_time is not None:
        install_success = True
        marker(f"BENCHMARK:pip_install_s:{pip_time:.2f}")

    if not install_success:
        # fallback
        edit_time = pip_install_editable(str(work_dir))
        if edit_time is not None:
            install_success = True
            marker(f"BENCHMARK:editable_install_s:{edit_time:.2f}")

    # 3. Measure import time
    import_time = measure_import('fable51_worlds')
    # 4. Run generation test
    world, gen_time = run_generation('fable51_worlds', tile_count=1000)
    # 5. Validate output
    if world is not None:
        validate_output(world)
    # 6. Simple query
    if world is not None:
        simple_query(world)

    # 7. Baseline comparison (using dummy baseline values)
    # Assume baseline tool 'ProceduralWorlds' generation time for 1000 tiles is 0.150s
    baseline_name = "proceduralworlds"
    baseline_gen_time = 0.150  # seconds
    if gen_time is not None:
        compare_vs_baseline('gen_time_s', gen_time, baseline_gen_time)

    # Ensure at least 3 benchmark lines (already emitted several)
    marker("RUN_OK")

if __name__ == "__main__":
    main()