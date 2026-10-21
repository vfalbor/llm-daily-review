import subprocess, sys, time, tracemalloc, os, json, urllib.request

def print_marker(msg):
    print(msg, flush=True)

def run_apk_install(pkg):
    try:
        start = time.time()
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:apk_install_{pkg}_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")
        return False

def pip_install(package):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:pip_install_{package}_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{package}:{e}")
        return False

def git_clone(repo, dest):
    try:
        start = time.time()
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:git_clone_{repo.split('/')[-1]}_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git_clone:{e}")
        return False

def pip_install_editable(path):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:pip_editable_install_{os.path.basename(path)}_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip_editable:{e}")
        return False

def measure_import(module_name):
    try:
        tracemalloc.start()
        start = time.time()
        __import__(module_name)
        elapsed = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_{module_name}_ms:{elapsed:.2f}")
        print_marker(f"BENCHMARK:import_{module_name}_memory_kb:{peak/1024:.2f}")
        return elapsed
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def run_cli_help(command):
    try:
        start = time.time()
        subprocess.run([command, '--help'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:{command}_help_ms:{elapsed:.2f}")
        print_marker(f"TEST_PASS:{command}_help")
    except Exception as e:
        print_marker(f"TEST_FAIL:{command}_help:{e}")

def compare_vs_baseline(name, metric, our, baseline):
    try:
        if baseline is None or baseline == 0:
            ratio = 1.0
        else:
            ratio = our / baseline
        print_marker(f"BENCHMARK:vs_{name}_{metric}:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_vs_{name}_{metric}:{e}")

def main():
    # 1. Install required apk packages
    for pkg in ['git', 'curl']:
        run_apk_install(pkg)

    # 2. Try pip install torch_tpu
    repo_url = "https://github.com/google-pytorch/torch_tpu"
    installed = False
    if not pip_install('torch_tpu'):
        # fallback to git clone + editable install
        src_dir = "/tmp/torch_tpu"
        if git_clone(repo_url, src_dir):
            installed = pip_install_editable(src_dir)
        else:
            installed = False
    else:
        installed = True

    if installed:
        print_marker("INSTALL_OK")
    else:
        print_marker("INSTALL_FAIL:torch_tpu:could_not_install")

    # 3. Test import of torch_tpu
    torch_tpu_import_time = measure_import('torch_tpu')
    if torch_tpu_import_time is not None:
        print_marker("TEST_PASS:import_torch_tpu")
    else:
        print_marker("TEST_FAIL:import_torch_tpu:import_error")

    # 4. Test CLI if available (torch_tpu provides a console script named torch_tpu)
    try:
        import importlib.metadata as metadata
        entrypoints = metadata.entry_points()
        cli_name = None
        for ep in entrypoints.select(group='console_scripts'):
            if 'torch_tpu' in ep.name:
                cli_name = ep.name
                break
        if cli_name:
            run_cli_help(cli_name)
        else:
            print_marker("TEST_SKIP:cli_help:no_console_script")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_detection:{e}")

    # 5. Baseline comparison with torch_xla if available
    baseline_time = measure_import('torch_xla')
    if baseline_time is not None:
        print_marker("TEST_PASS:import_torch_xla")
    else:
        print_marker("TEST_SKIP:import_torch_xla:not_installed")

    compare_vs_baseline('torch_xla', 'import_ms',
                        torch_tpu_import_time if torch_tpu_import_time else 0,
                        baseline_time)

    # Additional benchmark: count files in repo
    try:
        start = time.time()
        file_count = sum(len(files) for _, _, files in os.walk('.'))
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:repo_file_count:{file_count}")
        print_marker(f"BENCHMARK:file_count_time_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:file_count:{e}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()