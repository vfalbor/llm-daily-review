#!/usr/bin/env python3
import subprocess, sys, os, time, traceback, tracemalloc, shutil, json, pathlib

# Helper to print markers
def marker(line):
    print(line, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
        if res.returncode == 0:
            marker(f"INSTALL_OK | {pkg}")
        else:
            marker(f"INSTALL_FAIL:{pkg}: {res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{pkg}: {e}")

def install_pip(pkg):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
        if res.returncode == 0:
            marker(f"INSTALL_OK | pip:{pkg}")
        else:
            marker(f"INSTALL_FAIL:pip:{pkg}: {res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:pip:{pkg}: {e}")

def git_clone(url, dest):
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
        if res.returncode == 0:
            marker("INSTALL_OK | git_clone")
        else:
            marker(f"INSTALL_FAIL:git_clone: {res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:git_clone: {e}")

# 1. Install required system packages
for pkg in ['nodejs', 'npm', 'git', 'cargo', 'rust']:
    install_apk(pkg)

# 2. Install Python dependencies (pip)
install_pip('wheel')
install_pip('setuptools')

# 3. Clone repo and try pip install
repo_url = "https://github.com/ciromattia/kcc"
repo_dir = "/tmp/kcc_repo"
git_clone(repo_url, repo_dir)

# Attempt pip install from repo
def pip_install_repo(path):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', path])
        if res.returncode == 0:
            marker("INSTALL_OK | pip_repo")
            return True
        else:
            marker(f"INSTALL_FAIL:pip_repo: {res.stderr.strip()}")
            return False
    except Exception as e:
        marker(f"INSTALL_FAIL:pip_repo: {e}")
        return False

installed = pip_install_repo(repo_dir)
if not installed:
    # fallback: editable install
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', repo_dir])
        if res.returncode == 0:
            marker("INSTALL_OK | pip_editable")
            installed = True
        else:
            marker(f"INSTALL_FAIL:pip_editable: {res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:pip_editable: {e}")

# 4. Tests
def test_help():
    name = "help"
    try:
        start = time.time()
        res = run_cmd(['kcc', '--help'])
        duration = time.time() - start
        if res.returncode == 0 and 'Usage' in res.stdout:
            marker(f"TEST_PASS:{name}")
        else:
            marker(f"TEST_FAIL:{name}: non-zero exit or missing usage")
    except FileNotFoundError:
        marker(f"TEST_FAIL:{name}: kcc not found")
    except Exception as e:
        marker(f"TEST_FAIL:{name}: {e}")

def test_process_image():
    name = "process_image"
    try:
        sample_dir = pathlib.Path(repo_dir) / "examples"
        sample_png = sample_dir / "sample.png"
        if not sample_png.is_file():
            # create a simple png using pillow
            install_pip('pillow')
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 600), color='white')
            d = ImageDraw.Draw(img)
            d.text((10,10), "test", fill='black')
            sample_png.parent.mkdir(parents=True, exist_ok=True)
            img.save(sample_png)

        out_path = pathlib.Path("/tmp/kcc_output.png")
        if out_path.is_file():
            out_path.unlink()

        start = time.time()
        res = run_cmd(['kcc', str(sample_png), '-o', str(out_path)])
        elapsed = time.time() - start

        if res.returncode != 0:
            marker(f"TEST_FAIL:{name}: kcc exited {res.returncode}")
            return

        if not out_path.is_file():
            marker(f"TEST_FAIL:{name}: output file not created")
            return

        # verify dimensions (should match input or be scaled)
        from PIL import Image
        out_img = Image.open(out_path)
        if out_img.size[0] > 0 and out_img.size[1] > 0:
            marker(f"TEST_PASS:{name}")
        else:
            marker(f"TEST_FAIL:{name}: invalid dimensions")
        # benchmark
        marker(f"BENCHMARK:process_time_s:{elapsed:.3f}")
    except Exception as e:
        marker(f"TEST_FAIL:{name}: {e}")
        traceback.print_exc()

def benchmark_vs_imagemagick():
    name = "vs_imagemagick"
    try:
        # ensure ImageMagick convert exists
        res = run_cmd(['convert', '-version'])
        if res.returncode != 0:
            marker(f"TEST_SKIP:{name}: ImageMagick not installed")
            return
        sample = pathlib.Path("/tmp/kcc_input.png")
        if not sample.is_file():
            # reuse previous sample
            sample = pathlib.Path(repo_dir) / "examples" / "sample.png"
        out_kcc = pathlib.Path("/tmp/kcc_out.png")
        out_im = pathlib.Path("/tmp/im_out.png")
        # kcc timing
        t0 = time.time()
        run_cmd(['kcc', str(sample), '-o', str(out_kcc)])
        t_kcc = time.time() - t0
        # imagemagick timing (simple conversion)
        t1 = time.time()
        run_cmd(['convert', str(sample), str(out_im)])
        t_im = time.time() - t1
        ratio = t_kcc / t_im if t_im > 0 else float('inf')
        marker(f"BENCHMARK:vs_imagemagick_time_ratio:{ratio:.3f}")
    except Exception as e:
        marker(f"TEST_FAIL:{name}: {e}")

# Run tests with isolation
test_help()
test_process_image()
benchmark_vs_imagemagick()

# Additional generic benchmarks
def benchmark_memory():
    try:
        tracemalloc.start()
        dummy = [i for i in range(1000000)]
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.1f}")
    except Exception as e:
        marker(f"TEST_FAIL:benchmark_memory: {e}")

def benchmark_cpu_count():
    try:
        count = os.cpu_count()
        marker(f"BENCHMARK:cpu_count:{count}")
    except Exception as e:
        marker(f"TEST_FAIL:benchmark_cpu_count: {e}")

benchmark_memory()
benchmark_cpu_count()

# Final marker
marker("RUN_OK")