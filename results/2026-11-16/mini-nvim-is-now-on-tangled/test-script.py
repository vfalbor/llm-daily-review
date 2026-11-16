import subprocess, sys, time, tracemalloc, json, os, shutil, pathlib

def marker(msg):
    print(msg, flush=True)

def apk_add(pkg):
    start = time.time()
    result = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    duration = time.time() - start
    if result.returncode == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:apk {pkg} exit={result.returncode}")
    marker(f"BENCHMARK:apk_{pkg}_install_s:{duration:.3f}")

def pip_install(pkg):
    start = time.time()
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])
    duration = time.time() - start
    if result.returncode == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:pip {pkg} exit={result.returncode}")
    marker(f"BENCHMARK:pip_{pkg}_install_s:{duration:.3f}")
    return result.returncode == 0

def git_clone(repo, dest):
    start = time.time()
    result = subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    duration = time.time() - start
    if result.returncode == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:git clone {repo} exit={result.returncode}")
    marker(f"BENCHMARK:git_clone_s:{duration:.3f}")
    return result.returncode == 0

def pip_editable(path):
    start = time.time()
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path])
    duration = time.time() - start
    if result.returncode == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:pip -e {path} exit={result.returncode}")
    marker(f"BENCHMARK:pip_editable_s:{duration:.3f}")
    return result.returncode == 0

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        marker(f"TEST_PASS:import_{module_name}")
        marker(f"BENCHMARK:import_{module_name}_ms:{import_time:.2f}")
        return import_time
    except Exception as e:
        tracemalloc.stop()
        marker(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def run_neovim_benchmark(repo_path):
    # Minimal benchmark: start nvim in headless mode to source a config that loads mini.nvim
    nvim_cmd = [
        'nvim', '--headless', '-u', 'NONE', '-c',
        f"set rtp+={repo_path}|runtime plugin/mini.vim|lua require('mini.move')|qa"
    ]
    start = time.time()
    result = subprocess.run(nvim_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    duration_ms = (time.time() - start) * 1000
    if result.returncode == 0:
        marker(f"TEST_PASS:nvim_benchmark")
    else:
        marker(f"TEST_FAIL:nvim_benchmark:exit={result.returncode}")
    marker(f"BENCHMARK:nvim_startup_ms:{duration_ms:.2f}")
    return duration_ms

def compare_vs_baseline(metric, our_value, baseline_value):
    try:
        ratio = our_value / baseline_value if baseline_value else 0
        marker(f"BENCHMARK:vs_{baseline_value}_baseline_{metric}:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install system packages
    apk_add('git')

    # 2. Try pip install
    pip_success = pip_install('mini.nvim')
    repo_dir = pathlib.Path('/tmp/mini.nvim')
    if not pip_success:
        # fallback to git clone + editable install
        if git_clone('https://github.com/folke/mini.nvim.git', str(repo_dir)):
            pip_editable(str(repo_dir))

    # 3. Measure import time
    import_time = measure_import('mini')

    # 4. Run a minimal Neovim benchmark
    if repo_dir.is_dir():
        nvim_time = run_neovim_benchmark(str(repo_dir))
    else:
        nvim_time = None

    # 5. Emit additional benchmarks (placeholder counts)
    file_count = sum(1 for _ in pathlib.Path('.').rglob('*.py'))
    marker(f"BENCHMARK:loc_count:{file_count}")

    # 6. Compare against baseline (lazy.nvim assumed baseline install time ~5s)
    baseline_install = 5.0
    if import_time is not None:
        compare_vs_baseline('import_ms', import_time, baseline_install)

    # 7. Final marker
    marker("RUN_OK")

if __name__ == "__main__":
    main()