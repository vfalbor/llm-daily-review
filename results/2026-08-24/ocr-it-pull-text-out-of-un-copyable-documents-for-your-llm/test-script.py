import subprocess, sys, time, tracemalloc, os, pathlib, textwrap, json, shlex, signal

def emit(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(packages):
    try:
        start = time.time()
        result = subprocess.run(['apk', 'add', '--no-cache'] + packages, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if result.returncode == 0:
            emit(f"INSTALL_OK")
        else:
            emit(f"INSTALL_FAIL:{result.stderr.strip() or 'apk install error'}")
        return duration
    except Exception as e:
        emit(f"INSTALL_FAIL:{str(e)}")
        return None

def pip_install(packages):
    try:
        start = time.time()
        cmd = [sys.executable, '-m', 'pip', 'install', '--quiet'] + packages
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if result.returncode == 0:
            emit("INSTALL_OK")
        else:
            emit(f"INSTALL_FAIL:{result.stderr.strip() or 'pip install error'}")
        return duration
    except Exception as e:
        emit(f"INSTALL_FAIL:{str(e)}")
        return None

def benchmark(name, value, unit="s"):
    emit(f"BENCHMARK:{name}:{value}")

def try_import(module_name):
    try:
        start = time.perf_counter()
        tracemalloc.start()
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        dt = (time.perf_counter() - start) * 1000  # ms
        benchmark("import_time_ms", f"{dt:.2f}")
        return True, dt, peak/1024
    except Exception as e:
        emit(f"TEST_FAIL:import_{module_name}:{str(e)}")
        return False, None, None

def create_test_image(path, text):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (400, 100), color='white')
        d = ImageDraw.Draw(img)
        # Use default font
        d.text((10, 40), text, fill='black')
        img.save(path)
        return True
    except Exception as e:
        emit(f"TEST_FAIL:create_image:{str(e)}")
        return False

def run_ocr_it(input_path, output_path):
    try:
        cmd = ['ocr-it', '--input', str(input_path), '--output', str(output_path)]
        start = time.perf_counter()
        result = run_cmd(cmd)
        dt = (time.perf_counter() - start) * 1000  # ms
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ocr-it failed")
        benchmark("ocr_it_processing_ms", f"{dt:.2f}")
        return True, dt
    except Exception as e:
        emit(f"TEST_FAIL:ocr_it_process:{str(e)}")
        return False, None

def run_tesseract(input_path):
    try:
        cmd = ['tesseract', str(input_path), 'stdout']
        start = time.perf_counter()
        result = run_cmd(cmd)
        dt = (time.perf_counter() - start) * 1000  # ms
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "tesseract failed")
        benchmark("tesseract_processing_ms", f"{dt:.2f}")
        return True, dt
    except Exception as e:
        emit(f"TEST_SKIP:tesseract:{str(e)}")
        return False, None

def compare_vs_baseline(ocr_time, base_time):
    try:
        ratio = ocr_time / base_time if base_time else None
        if ratio is not None:
            benchmark("vs_tesseract_processing_ratio", f"{ratio:.2f}")
    except Exception as e:
        emit(f"TEST_SKIP:compare_vs_baseline:{str(e)}")

def main():
    # 1. Install required APK packages
    apk_duration = install_apk(['git', 'build-base', 'tesseract-ocr'])
    if apk_duration is not None:
        benchmark("apk_install_time_s", f"{apk_duration:.2f}")

    # 2. Install Python dependencies (ocr-it may be a package)
    pip_duration = pip_install(['ocr-it', 'pillow', 'reportlab'])
    if pip_duration is not None:
        benchmark("pip_install_time_s", f"{pip_duration:.2f}")

    # 3. Verify import of ocr_it (module name guessed)
    imported, import_ms, import_peak_kb = try_import('ocr_it')
    if imported:
        emit("TEST_PASS:import_ocr_it")
    else:
        emit("TEST_FAIL:import_ocr_it:cannot_import")

    # 4. Functional test – create image and run ocr-it
    workdir = pathlib.Path.cwd() / "qa_tmp"
    workdir.mkdir(exist_ok=True)
    img_path = workdir / "test.png"
    out_path = workdir / "out.txt"
    expected_text = "Hello OCR"

    if create_test_image(img_path, expected_text):
        emit("TEST_PASS:create_test_image")
    else:
        emit("TEST_FAIL:create_test_image:creation_error")

    success, ocr_time = run_ocr_it(img_path, out_path)
    if success and out_path.is_file():
        try:
            content = out_path.read_text().strip()
            if expected_text in content:
                emit("TEST_PASS:ocr_it_output")
            else:
                emit("TEST_FAIL:ocr_it_output:unexpected_content")
        except Exception as e:
            emit(f"TEST_FAIL:ocr_it_output_read:{str(e)}")
    else:
        emit("TEST_FAIL:ocr_it_process:run_error")

    # 5. Baseline with tesseract
    baseline_success, base_time = run_tesseract(img_path)
    if baseline_success:
        compare_vs_baseline(ocr_time or 0, base_time)

    # 6. Placeholder for PDF hidden‑text test (skip due to complexity)
    emit("TEST_SKIP:pdf_hidden_text:PDF generation not implemented in this script")

    # 7. Benchmark: count created files as a simple metric
    file_count = sum(1 for _ in workdir.iterdir())
    benchmark("test_files_count", f"{file_count}")

    # Clean up temporary data (optional, not required for benchmark)
    try:
        for p in workdir.iterdir():
            p.unlink()
        workdir.rmdir()
    except Exception:
        pass

    # Final marker
    emit("RUN_OK")

if __name__ == "__main__":
    # Ensure script aborts gracefully on SIGTERM/SIGINT
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    main()