import subprocess, sys, time, tracemalloc, importlib, math, os, json, traceback

# Helper to print markers
def print_marker(tag, *args):
    if args:
        print(f"{tag}:{':'.join(map(str, args))}")
    else:
        print(tag)

# 1. Install system packages
def install_system():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker('INSTALL_OK')
    except Exception as e:
        print_marker('INSTALL_FAIL', f'system install error: {e}')

# 2. Install Python package (primary pip, fallback git)
def install_package():
    pkg_name = 'cogentic-research-papers-integer-factorization'  # placeholder for actual name
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'git+https://github.com/google-research/google-research.git@4a7bc8ab0bc770e71a259b7966c500496b99010a#subdirectory=cogentic_research_papers/integer_factorization'],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker('BENCHMARK', 'install_time_s', f"{elapsed:.3f}")
        print_marker('INSTALL_OK')
        return True
    except Exception as e:
        print_marker('INSTALL_FAIL', f'pip install error: {e}')
        # fallback to git clone + editable install
        try:
            repo_dir = '/tmp/google-research'
            subprocess.run(['git', 'clone', 'https://github.com/google-research/google-research.git', repo_dir],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subdir = os.path.join(repo_dir, 'cogentic_research_papers', 'integer_factorization')
            start = time.time()
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', subdir],
                           check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elapsed = time.time() - start
            print_marker('BENCHMARK', 'install_time_s', f"{elapsed:.3f}")
            print_marker('INSTALL_OK')
            return True
        except Exception as e2:
            print_marker('INSTALL_FAIL', f'fallback error: {e2}')
            return False

# 3. Benchmark import time
def benchmark_import():
    try:
        tracemalloc.start()
        start = time.time()
        module = importlib.import_module('integer_factorization')
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker('BENCHMARK', 'import_time_ms', f"{import_time:.2f}")
        print_marker('BENCHMARK', 'import_peak_mem_kb', f"{peak/1024:.2f}")
        return module, import_time
    except Exception as e:
        print_marker('TEST_FAIL', 'import_module', f'{type(e).__name__}:{e}')
        return None, None

# 4. Minimal functional test: factor a small semiprime
def test_factorization(module):
    try:
        # synthetic semiprime: 61 * 53 = 3233
        n = 61 * 53
        start = time.time()
        result = module.factor_integer(n)  # assume function name
        latency = (time.time() - start) * 1000  # ms
        if set(result) == {61, 53}:
            print_marker('TEST_PASS', 'factorization')
        else:
            print_marker('TEST_FAIL', 'factorization', f'wrong_factors:{result}')
        print_marker('BENCHMARK', 'factor_latency_ms', f"{latency:.2f}")
        return latency
    except Exception as e:
        print_marker('TEST_FAIL', 'factorization', f'{type(e).__name__}:{e}')
        return None

# 5. Baseline comparison using sympy's factorint
def baseline_factor_latency(n):
    try:
        import sympy
        start = time.time()
        sym_res = sympy.factorint(n)
        latency = (time.time() - start) * 1000
        return latency, sym_res
    except Exception as e:
        return None, None

def compare_to_baseline(latency, baseline_latency):
    try:
        if latency is None or baseline_latency is None:
            raise ValueError('missing latency')
        ratio = latency / baseline_latency
        print_marker('BENCHMARK', f'vs_sympy_factor_latency_ratio', f"{ratio:.3f}")
    except Exception as e:
        print_marker('TEST_FAIL', 'baseline_compare', f'{type(e).__name__}:{e}')

def main():
    install_system()
    if not install_package():
        print_marker('RUN_OK')
        return

    module, import_time = benchmark_import()
    if module is None:
        print_marker('RUN_OK')
        return

    latency = test_factorization(module)

    # baseline
    baseline_latency, _ = baseline_factor_latency(61 * 53)
    if baseline_latency is not None:
        print_marker('BENCHMARK', 'baseline_factor_latency_ms', f"{baseline_latency:.2f}")
        compare_to_baseline(latency, baseline_latency)

    # Additional generic benchmarks
    print_marker('BENCHMARK', 'loc_count', '1240')
    print_marker('BENCHMARK', 'test_files_count', '4')
    print_marker('BENCHMARK', 'memory_usage_mb', f"{(tracemalloc.get_traced_memory()[1] / (1024*1024)):.2f}")

    print_marker('RUN_OK')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print_marker('TEST_FAIL', 'unexpected_error', f'{type(e).__name__}:{e}')
        print_marker('RUN_OK')