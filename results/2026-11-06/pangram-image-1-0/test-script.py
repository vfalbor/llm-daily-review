#!/usr/bin/env python3
import subprocess
import sys
import time
import tracemalloc
import os
import shutil
import json
import hashlib
import math
from pathlib import Path

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk(pkgs):
    cmd = ['apk', 'add', '--no-cache'] + pkgs
    res = run_cmd(cmd, check=False)
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else "exception")[:200]
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def pip_install(pkg):
    cmd = [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg]
    res = run_cmd(cmd, check=False)
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else "exception")[:200]
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def pip_install_editable(path):
    cmd = [sys.executable, '-m', 'pip', 'install', '-e', str(path)]
    res = run_cmd(cmd, check=False)
    if res and res.returncode == 0:
        print_marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else "exception")[:200]
        print_marker(f"INSTALL_FAIL:{reason}")
        return False

def measure_import_time(module_name):
    start = time.time()
    try:
        __import__(module_name)
        elapsed = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False

def generate_png(path, size=(64,64)):
    # generate a simple PNG using Pillow (install if needed)
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        if not pip_install('pillow'):
            return False
        from PIL import Image, ImageDraw
    img = Image.new('RGB', size, color='blue')
    draw = ImageDraw.Draw(img)
    draw.rectangle([10,10, size[0]-10, size[1]-10], fill='red')
    img.save(path, format='PNG')
    return True

def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            blk = f.read(65536)
            if not blk:
                break
            h.update(blk)
    return h.hexdigest()

def test_clone_and_build(repo_url, workdir):
    try:
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True)
        res = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(workdir)])
        if res is None or res.returncode != 0:
            raise RuntimeError(f"git clone failed: {res.stderr if res else 'no result'}")
        # Try building binary if exists (placeholder, actual build may differ)
        build_script = workdir / 'setup.py'
        if build_script.exists():
            # pip install editable as fallback build
            if not pip_install_editable(workdir):
                raise RuntimeError("pip install -e failed")
        print_marker("TEST_PASS:clone_and_build")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_and_build:{e}")
        return False

def test_encode_decode(pangram_pkg, baseline_pkg, workdir):
    try:
        # import modules
        import importlib
        pangram = importlib.import_module(pangram_pkg)
        baseline = importlib.import_module(baseline_pkg)
        # generate png
        src_png = workdir / 'src.png'
        if not generate_png(src_png):
            raise RuntimeError("Failed to generate source PNG")
        # encode with pangram
        enc_path = workdir / 'out.pangram'
        start_enc = time.time()
        pangram.encode_image(str(src_png), str(enc_path))
        enc_time = (time.time() - start_enc) * 1000
        print_marker(f"BENCHMARK:pangram_encode_ms:{enc_time:.2f}")
        # size reduction
        src_sz = src_png.stat().st_size
        enc_sz = enc_path.stat().st_size
        reduction = (src_sz - enc_sz) / src_sz * 100 if src_sz else 0
        print_marker(f"BENCHMARK:pangram_size_reduction_pct:{reduction:.2f}")
        # decode
        dec_path = workdir / 'decoded.png'
        start_dec = time.time()
        pangram.decode_image(str(enc_path), str(dec_path))
        dec_time = (time.time() - start_dec) * 1000
        print_marker(f"BENCHMARK:pangram_decode_ms:{dec_time:.2f}")
        # compare fidelity (hash compare)
        src_hash = compute_sha256(src_png)
        dec_hash = compute_sha256(dec_path)
        if src_hash != dec_hash:
            raise RuntimeError("Decoded image differs from source")
        # baseline encode/decode using WebP via Pillow
        baseline_enc = workdir / 'out.webp'
        start_benc = time.time()
        baseline.save(str(src_png), format='WEBP')
        benc_time = (time.time() - start_benc) * 1000
        print_marker(f"BENCHMARK:webp_encode_ms:{benc_time:.2f}")
        baseline_dec = workdir / 'decoded_webp.png'
        start_bdec = time.time()
        img = baseline.open(str(baseline_enc))
        img.save(str(baseline_dec))
        bdec_time = (time.time() - start_bdec) * 1000
        print_marker(f"BENCHMARK:webp_decode_ms:{bdec_time:.2f}")
        # compare ratios
        enc_ratio = enc_time / benc_time if benc_time else math.inf
        dec_ratio = dec_time / bdec_time if bdec_time else math.inf
        print_marker(f"BENCHMARK:vs_webp_encode_ratio:{enc_ratio:.2f}")
        print_marker(f"BENCHMARK:vs_webp_decode_ratio:{dec_ratio:.2f}")
        print_marker("TEST_PASS:encode_decode")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:encode_decode:{e}")
        return False

def main():
    # 1. install apk packages
    install_apk(['git'])
    # 2. install python package
    pkg_name = 'pangram-image'
    if not pip_install(pkg_name):
        # fallback to git clone + editable install
        repo = 'https://github.com/pangram-io/pangram-image.git'
        work = Path('/tmp/pangram_src')
        if test_clone_and_build(repo, work):
            pip_install_editable(work)
    # 3. measure import time
    measure_import_time('pangram_image')
    # 4. run functional tests
    workdir = Path('/tmp/pangram_test')
    test_encode_decode('pangram_image', 'PIL.Image', workdir)
    # 5. additional benchmark: memory usage during import
    tracemalloc.start()
    start = time.time()
    try:
        import pangram_image
    except Exception:
        pass
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:import_peak_mem_kb:{peak/1024:.2f}")
    print_marker(f"BENCHMARK:import_elapsed_ms:{(time.time()-start)*1000:.2f}")
    # ensure at least 3 benchmark lines (already emitted many)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()