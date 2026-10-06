import subprocess, sys, time, tracemalloc, json, os, math, pathlib

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode() or e.stdout.decode()

def install_apk(packages):
    success, out = run_cmd(['apk', 'add', '--no-cache'] + packages)
    if success:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{out.strip()}")
    return success

def pip_install(package):
    success, out = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package])
    if success:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{out.strip()}")
    return success

def git_clone(repo, dest):
    success, out = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    if not success:
        print(f"INSTALL_FAIL:{out.strip()}")
    return success

def fallback_install_from_source(repo_url):
    src_dir = "/tmp/deda_src"
    if os.path.isdir(src_dir):
        subprocess.run(['rm', '-rf', src_dir])
    if not git_clone(repo_url, src_dir):
        return False
    success, out = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', src_dir])
    if success:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{out.strip()}")
    return success

def benchmark(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*args, **kwargs)
        success = True
    except Exception as e:
        result = None
        success = False
        err = str(e)
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = end - start
    print(f"BENCHMARK:{name}:{elapsed:.4f}")
    return success, result, elapsed, peak

def import_module(name):
    __import__(name)

def test_import():
    name = "deda"
    start = time.time()
    try:
        import_module(name)
        print(f"TEST_PASS:{name}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")
        return False
    finally:
        elapsed = time.time() - start
        print(f"BENCHMARK:import_time_s:{elapsed:.4f}")

def generate_synthetic_image():
    # create a tiny black-white dot pattern using Pillow (install if needed)
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        pip_install('pillow')
        from PIL import Image, ImageDraw
    img = Image.new('L', (100, 100), color=0)
    draw = ImageDraw.Draw(img)
    for i in range(10, 90, 20):
        draw.ellipse((i, i, i+5, i+5), fill=255)
    path = "/tmp/synthetic.png"
    img.save(path)
    return path

def test_core_operation():
    test_name = "core_operation"
    try:
        import deda
    except Exception as e:
        print(f"TEST_FAIL:{test_name}:{e}")
        return
    img_path = generate_synthetic_image()
    start = time.time()
    try:
        # Assuming deda provides a function `process_image(path)` returning results
        result = deda.process_image(img_path)
        elapsed = time.time() - start
        print(f"BENCHMARK:core_latency_s:{elapsed:.4f}")
        if result is not None:
            print(f"TEST_PASS:{test_name}")
        else:
            print(f"TEST_FAIL:{test_name}:No result")
    except Exception as e:
        elapsed = time.time() - start
        print(f"BENCHMARK:core_latency_s:{elapsed:.4f}")
        print(f"TEST_FAIL:{test_name}:{e}")

def baseline_opencv_latency(image_path):
    import cv2, numpy as np
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    start = time.time()
    # simple blob detection as a placeholder
    detector = cv2.SimpleBlobDetector_create()
    keypoints = detector.detect(img)
    return time.time() - start

def benchmark_vs_opencv():
    img_path = generate_synthetic_image()
    # our tool latency already measured in test_core_operation, reuse
    # here we just recompute for fairness
    try:
        import deda
        our_start = time.time()
        _ = deda.process_image(img_path)
        our_elapsed = time.time() - our_start
    except Exception:
        our_elapsed = float('nan')
    try:
        opencv_elapsed = baseline_opencv_latency(img_path)
    except Exception:
        opencv_elapsed = float('nan')
    if not math.isnan(our_elapsed) and not math.isnan(opencv_elapsed) and opencv_elapsed > 0:
        ratio = our_elapsed / opencv_elapsed
        print(f"BENCHMARK:vs_opencv_latency_ratio:{ratio:.4f}")
    else:
        print(f"BENCHMARK:vs_opencv_latency_ratio:NaN")

def main():
    # 1. Install required system packages
    install_apk(['git'])

    # 2. Install the Python package
    if not pip_install('deda'):
        # fallback to source
        fallback_install_from_source('https://github.com/dfd-tud/deda.git')

    # 3. Run tests
    test_import()
    test_core_operation()
    benchmark_vs_opencv()

    # Additional generic benchmarks
    # Count of files in the package
    try:
        import deda
        pkg_path = pathlib.Path(deda.__file__).parent
        file_count = sum(1 for _ in pkg_path.rglob('*') if _.is_file())
        print(f"BENCHMARK:package_file_count:{file_count}")
    except Exception as e:
        print(f"BENCHMARK:package_file_count:0")

    # Memory usage after import (peak)
    tracemalloc.start()
    try:
        import_module('deda')
    except Exception:
        pass
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:import_peak_memory_bytes:{peak}")

    print("RUN_OK")

if __name__ == "__main__":
    main()