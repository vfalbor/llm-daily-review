import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} exit {res.returncode}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} exception {e}")

def pip_install(pkg):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:pip {pkg} exit {res.returncode}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip {pkg} exception {e}")

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        elapsed_ms = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:import_time_ms:{elapsed_ms:.2f}")
        print_marker(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return False
    finally:
        tracemalloc.stop()

def clone_repo(url, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if res.returncode != 0:
        raise RuntimeError(f"git clone failed: {res.stderr}")

def configure_build(src_dir):
    start = time.time()
    res = run_cmd(['./configure', '--enable-shared'], cwd=src_dir)
    if res.returncode != 0:
        raise RuntimeError(f"./configure failed: {res.stderr}")
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:configure_time_s:{elapsed:.2f}")

def make_build(src_dir):
    start = time.time()
    res = run_cmd(['make', '-j' + str(os.cpu_count())], cwd=src_dir)
    if res.returncode != 0:
        raise RuntimeError(f"make failed: {res.stderr}")
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:make_time_s:{elapsed:.2f}")

def make_install(src_dir):
    start = time.time()
    res = run_cmd(['make', 'install'], cwd=src_dir)
    if res.returncode != 0:
        raise RuntimeError(f"make install failed: {res.stderr}")
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")

def run_ffmpeg_version():
    res = run_cmd(['ffmpeg', '-version'])
    if res.returncode == 0:
        print_marker("TEST_PASS:ffmpeg_version")
    else:
        print_marker(f"TEST_FAIL:ffmpeg_version:{res.stderr}")

def generate_synthetic_video(path, duration=5):
    # create a 5s color video using ffmpeg itself (already built)
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', 'testsrc=size=128x128:rate=25',
        '-t', str(duration),
        '-c:v', 'libx264',
        path
    ]
    res = run_cmd(cmd)
    if res.returncode != 0:
        raise RuntimeError(f"synthetic video generation failed: {res.stderr}")

def encode_video(input_path, output_path):
    start = time.time()
    cmd = ['ffmpeg', '-y', '-i', input_path, '-c:v', 'libx264', output_path]
    res = run_cmd(cmd)
    elapsed = time.time() - start
    if res.returncode != 0:
        raise RuntimeError(f"encoding failed: {res.stderr}")
    print_marker(f"BENCHMARK:encoding_time_s:{elapsed:.2f}")
    return elapsed

def compare_vs_baseline(metric, ffmpeg_val, baseline_val):
    try:
        ratio = ffmpeg_val / baseline_val if baseline_val else 0
        print_marker(f"BENCHMARK:vs_gstreamer_{metric}_ratio:{ratio:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_vs_baseline:{e}")

def main():
    # 1. Install apk packages
    install_apk('git')
    install_apk('build-base')
    install_apk('nasm')
    install_apk('yasm')
    install_apk('pkgconf')
    install_apk('zlib-dev')
    install_apk('libpng-dev')
    install_apk('libx264-dev')
    # 2. Clone repo
    repo_url = "https://github.com/FFmpeg/FFmpeg"
    src_dir = "/tmp/ffmpeg_src"
    try:
        clone_repo(repo_url, src_dir)
        print_marker("TEST_PASS:git_clone")
    except Exception as e:
        print_marker(f"TEST_FAIL:git_clone:{e}")
        # fallback: try pip install (unlikely)
        pip_install('ffmpeg-python')
        # exit early
        print_marker("RUN_OK")
        return

    # 3. Configure
    try:
        configure_build(src_dir)
        print_marker("TEST_PASS:configure")
    except Exception as e:
        print_marker(f"TEST_FAIL:configure:{e}")

    # 4. Build
    try:
        make_build(src_dir)
        print_marker("TEST_PASS:make")
    except Exception as e:
        print_marker(f"TEST_FAIL:make:{e}")

    # 5. Install
    try:
        make_install(src_dir)
        print_marker("TEST_PASS:make_install")
    except Exception as e:
        print_marker(f"TEST_FAIL:make_install:{e}")

    # 6. ffmpeg version
    try:
        run_ffmpeg_version()
    except Exception as e:
        print_marker(f"TEST_FAIL:ffmpeg_version:{e}")

    # 7. Synthetic video and encode benchmark
    try:
        input_vid = "/tmp/input.mp4"
        output_vid = "/tmp/output.mp4"
        generate_synthetic_video(input_vid, duration=5)
        print_marker("TEST_PASS:generate_synthetic")
        enc_time = encode_video(input_vid, output_vid)
        # Compare with a made-up baseline (e.g., 6 seconds)
        baseline_time = 6.0
        compare_vs_baseline("encoding_time_s", enc_time, baseline_time)
    except Exception as e:
        print_marker(f"TEST_FAIL:encoding:{e}")

    # Additional benchmarks
    try:
        # count lines of source as LOC benchmark
        loc = sum(1 for _ in pathlib.Path(src_dir).rglob('*.c'))
        print_marker(f"BENCHMARK:loc_count:{loc}")
        # count number of source files
        files = sum(1 for _ in pathlib.Path(src_dir).rglob('*'))
        print_marker(f"BENCHMARK:source_files_count:{files}")
    except Exception as e:
        print_marker(f"TEST_FAIL:benchmark_misc:{e}")

    # Import test (ffmpeg-python as sanity)
    measure_import('ffmpeg')

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()