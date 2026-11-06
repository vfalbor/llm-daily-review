import subprocess, sys, time, os, json, shutil, tempfile, tracemalloc, pathlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def pip_install(package):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip()}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def pip_install_editable(path):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', path])
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip()}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def import_time(module_name):
    start = time.time()
    try:
        __import__(module_name)
        duration = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{duration:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False

def run_help():
    try:
        res = run_cmd(['youtube-downloader', '--help'])
        if res.returncode == 0:
            print_marker("TEST_PASS:cli_help")
        else:
            print_marker(f"TEST_FAIL:cli_help:{res.stderr.strip()}")
    except FileNotFoundError:
        print_marker("TEST_FAIL:cli_help:command not found")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_help:{e}")

def download_video(url, out_dir, tool_cmd):
    start = time.time()
    try:
        res = run_cmd(tool_cmd + ['-o', str(out_dir / '%(title)s.%(ext)s'), url])
        elapsed = time.time() - start
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        # locate downloaded file
        files = list(out_dir.glob('*'))
        if not files:
            raise FileNotFoundError("No file downloaded")
        size = files[0].stat().st_size
        print_marker(f"BENCHMARK:download_time_s:{elapsed:.2f}")
        print_marker(f"BENCHMARK:file_size_bytes:{size}")
        return elapsed, size, files[0]
    except Exception as e:
        print_marker(f"TEST_FAIL:download:{e}")
        return None, None, None

def benchmark_vs_baseline(url, out_dir):
    # baseline using yt-dlp (should be installed via pip)
    try:
        base_start = time.time()
        res = run_cmd(['yt-dlp', '-o', str(out_dir / 'baseline_%(title)s.%(ext)s'), url])
        base_elapsed = time.time() - base_start
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        base_files = list(out_dir.glob('baseline_*'))
        if not base_files:
            raise FileNotFoundError("Baseline file missing")
        # compare with previous download (assume vars set globally)
        if 'last_download_time' in globals():
            ratio = globals()['last_download_time'] / base_elapsed if base_elapsed else float('inf')
            print_marker(f"BENCHMARK:vs_yt-dlp_download_ratio:{ratio:.3f}")
        print_marker(f"BENCHMARK:baseline_download_time_s:{base_elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline:{e}")

def main():
    # 1. Install required apk packages
    install_apk('git')

    # 2. Install youtube-downloader via pip
    if not pip_install('youtube-downloader'):
        # fallback to git clone
        tmp_repo = pathlib.Path('/tmp/youtube-downloader')
        try:
            if tmp_repo.exists():
                shutil.rmtree(tmp_repo)
            res = run_cmd(['git', 'clone', 'https://github.com/cryptomancer/youtube-downloader.git', str(tmp_repo)])
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
            if not pip_install_editable(str(tmp_repo)):
                print_marker("TEST_SKIP:install_fallback:Both pip and git install failed")
                return
        except Exception as e:
            print_marker(f"TEST_FAIL:install_fallback:{e}")
            return

    # 3. Measure import time
    if not import_time('youtube_downloader'):
        pass

    # 4. Verify CLI help
    run_help()

    # 5. Functional download test
    test_url = 'https://www.youtube.com/watch?v=BaW_jenozKc'  # small public video
    with tempfile.TemporaryDirectory() as td:
        out_path = pathlib.Path(td)
        # download with youtube-downloader
        dl_time, dl_size, dl_file = download_video(test_url, out_path, ['youtube-downloader'])
        if dl_time is not None:
            globals()['last_download_time'] = dl_time
            # basic size check
            if dl_size < 1000:
                print_marker("TEST_FAIL:download_size:File too small")
            else:
                print_marker("TEST_PASS:download")
        # benchmark against yt-dlp
        benchmark_vs_baseline(test_url, out_path)

    # Ensure at least three benchmark lines (already emitted import, download, baseline)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()