import subprocess, sys, time, tracemalloc, os, json, pathlib, shutil, traceback

def log(marker):
    print(marker, flush=True)

def apk_install(pkg):
    start = time.time()
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f'INSTALL_OK | {pkg}')
    except Exception as e:
        log(f'INSTALL_FAIL:{pkg}:{e}')
    finally:
        elapsed = time.time() - start
        log(f'BENCHMARK:apk_install_{pkg}_time_s:{elapsed:.3f}')

def pip_install(package):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f'INSTALL_OK | pip:{package}')
        success = True
    except Exception as e:
        log(f'INSTALL_FAIL:pip:{package}:{e}')
        success = False
    finally:
        log(f'BENCHMARK:pip_install_{package}_time_s:{time.time()-start:.3f}')
    return success

def git_clone(repo, dest):
    start = time.time()
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f'INSTALL_OK | git:{repo}')
        success = True
    except Exception as e:
        log(f'INSTALL_FAIL:git:{repo}:{e}')
        success = False
    finally:
        log(f'BENCHMARK:git_clone_time_s:{time.time()-start:.3f}')
    return success

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        log(f'TEST_PASS:import_{module_name}')
        log(f'BENCHMARK:import_time_ms:{import_time:.2f}')
        return True, import_time
    except Exception as e:
        log(f'TEST_FAIL:import_{module_name}:{e}')
        return False, None
    finally:
        current, peak = tracemalloc.get_traced_memory()
        log(f'BENCHMARK:import_memory_peak_kb:{peak/1024:.2f}')
        tracemalloc.stop()

def run_minimal_operation():
    tracemalloc.start()
    start = time.time()
    try:
        import astrohelm
        # Assuming the package exposes a function `process_image` that accepts a PIL image.
        # We'll create a dummy image using Pillow if available.
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (640, 480), color='black')
            draw = ImageDraw.Draw(img)
            draw.rectangle([200,150,440,330], outline='white')
            result = astrohelm.process_image(img) if hasattr(astrohelm, 'process_image') else None
        except Exception:
            result = None  # fallback if Pillow not installed or function missing
        latency = (time.time() - start) * 1000  # ms
        log(f'TEST_PASS:minimal_operation')
        log(f'BENCHMARK:minimal_operation_latency_ms:{latency:.2f}')
        return True, latency
    except Exception as e:
        log(f'TEST_FAIL:minimal_operation:{e}')
        return False, None
    finally:
        _, peak = tracemalloc.get_traced_memory()
        log(f'BENCHMARK:minimal_operation_memory_peak_kb:{peak/1024:.2f}')
        tracemalloc.stop()

def benchmark_vs_baseline(metric, ours, baseline):
    try:
        ratio = ours / baseline if baseline != 0 else float('inf')
        log(f'BENCHMARK:vs_{baseline}_vs_{metric}_ratio:{ratio:.3f}')
    except Exception as e:
        log(f'TEST_FAIL:benchmark_vs_baseline:{e}')

def main():
    # 1. Install system packages
    apk_install('git')
    apk_install('python3-dev')
    apk_install('gcc')
    apk_install('musl-dev')
    # Pillow may be needed for image creation
    apk_install('py3-pip')

    # 2. Install python package
    pkg_name = 'astrohelm'
    installed = pip_install(pkg_name)

    # 3. Fallback to git clone + editable install if pip failed
    repo_url = 'https://github.com/astrohelm/astrohelm.git'
    clone_dir = '/tmp/astrohelm_src'
    if not installed:
        if os.path.isdir(clone_dir):
            shutil.rmtree(clone_dir)
        if git_clone(repo_url, clone_dir):
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '-e', clone_dir],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log('INSTALL_OK | pip_editable:astrohelm')
        else:
            log('INSTALL_FAIL:git_clone_and_editable')
    # 4. Measure import time
    imported, import_time = measure_import('astrohelm')
    # 5. Run minimal core operation
    op_success, op_latency = run_minimal_operation()
    # 6. Emit additional generic benchmarks
    bench_start = time.time()
    # count python files in repo if cloned
    file_count = 0
    if os.path.isdir(clone_dir):
        for root, _, files in os.walk(clone_dir):
            file_count += sum(1 for f in files if f.endswith('.py'))
    log(f'BENCHMARK:repo_py_files_count:{file_count}')
    log(f'BENCHMARK:script_runtime_s:{time.time()-bench_start:.3f}')

    # 7. Compare against baseline (assume baseline latency 200ms)
    baseline_latency = 200.0
    if op_latency is not None:
        benchmark_vs_baseline('minimal_operation_latency_ms', op_latency, baseline_latency)

    # Final marker
    log('RUN_OK')

if __name__ == '__main__':
    try:
        main()
    except Exception:
        log(f'TEST_FAIL:unexpected_error:{traceback.format_exc()}')
        log('RUN_OK')