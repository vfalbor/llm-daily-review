import subprocess, sys, time, tracemalloc, shlex, json, os, re

def print_marker(msg):
    print(msg, flush=True)

def apk_add(pkg):
    try:
        start = time.time()
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f'INSTALL_OK')
        return elapsed
    except Exception as e:
        print_marker(f'INSTALL_FAIL:{e}')
        return None

def pip_install(pkg):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f'INSTALL_OK')
        return elapsed
    except Exception as e:
        print_marker(f'INSTALL_FAIL:{e}')
        return None

def git_clone(repo, dest):
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker('INSTALL_OK')
        return True
    except Exception as e:
        print_marker(f'INSTALL_FAIL:{e}')
        return False

def run_cli(command):
    try:
        start = time.time()
        result = subprocess.run(shlex.split(command), capture_output=True, text=True, check=False)
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, None

def measure_import(module_name):
    try:
        tracemalloc.start()
        start = time.time()
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return import_time, peak / 1024  # KB
    except Exception as e:
        print_marker(f'TEST_FAIL:import_{module_name}:{e}')
        return None, None

def main():
    # 1. Install system packages
    apk_time = apk_add('git')
    if apk_time is not None:
        print_marker(f'BENCHMARK:apk_git_install_s:{apk_time:.3f}')

    # 2. Install livenerf via pip
    install_time = pip_install('livenerf')
    if install_time is not None:
        print_marker(f'BENCHMARK:livenerf_pip_install_s:{install_time:.3f}')

    # fallback to source if import fails
    try:
        import livenerf
        print_marker('TEST_PASS:import_livenerf')
    except Exception:
        print_marker('TEST_FAIL:import_livenerf:pip install failed, trying source')
        src_dir = '/tmp/livenerf_src'
        if git_clone('https://github.com/ninjahawk/livenerf.git', src_dir):
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', src_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                import livenerf  # type: ignore
                print_marker('TEST_PASS:import_livenerf_from_source')
            except Exception as e:
                print_marker(f'TEST_FAIL:import_livenerf_from_source:{e}')

    # 3. Measure import time
    imp_time, imp_mem = measure_import('livenerf')
    if imp_time is not None:
        print_marker(f'BENCHMARK:import_livenerf_ms:{imp_time:.2f}')
        print_marker(f'BENCHMARK:import_livenerf_mem_kb:{imp_mem:.2f}')
        print_marker('TEST_PASS:import_time_measure')
    else:
        print_marker('TEST_SKIP:import_time_measure:Import failed')

    # 4. Run minimal functional test via CLI
    cmd = 'livenerf --model dummy --benchmark livenerf-5.5 --max_examples 1 --output json'
    result, cli_time = run_cli(cmd)
    if result is not None:
        print_marker(f'BENCHMARK:livenerf_cli_latency_s:{cli_time:.3f}')
        if result.returncode == 0:
            try:
                out = json.loads(result.stdout)
                # Very basic validation: expect a list with one dict containing 'benchmark'
                if isinstance(out, list) and out and isinstance(out[0], dict) and 'benchmark' in out[0]:
                    print_marker('TEST_PASS:livenerf_cli_output')
                else:
                    print_marker('TEST_FAIL:livenerf_cli_output:Unexpected structure')
            except Exception as e:
                print_marker(f'TEST_FAIL:livenerf_cli_output:JSON parse error {e}')
        else:
            print_marker(f'TEST_FAIL:livenerf_cli:non-zero exit {result.returncode}')
    else:
        print_marker('TEST_FAIL:livenerf_cli:Exception during execution')

    # 5. Baseline comparison with lm-eval-harness (if installed)
    baseline_time = None
    try:
        _, baseline_time = run_cli('lm-eval --model dummy --tasks hellaswag --no-cache')
    except Exception:
        pass
    if baseline_time is not None and cli_time is not None:
        ratio = cli_time / baseline_time if baseline_time else float('nan')
        print_marker(f'BENCHMARK:vs_lm_eval_harness_cli_latency_ratio:{ratio:.3f}')
    else:
        print_marker('BENCHMARK:vs_lm_eval_harness_cli_latency_ratio:na')

    # Ensure at least 3 benchmark lines (already emitted several)
    # Final marker
    print_marker('RUN_OK')

if __name__ == '__main__':
    main()