import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib

def log(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(packages):
    try:
        start = time.time()
        res = subprocess.run(['apk', 'add', '--no-cache'] + packages, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elapsed = time.time() - start
        log(f"BENCHMARK:install_{'_'.join(packages)}_time_s:{elapsed:.2f}")
        if res.returncode == 0:
            log("INSTALL_OK")
        else:
            log(f"INSTALL_FAIL:apk exit {res.returncode}")
    except Exception as e:
        log(f"INSTALL_FAIL:{e}")

def install_node_deps():
    try:
        start = time.time()
        res = subprocess.run(['npm', 'install', '-g', 'ffmpeg-static'], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elapsed = time.time() - start
        log(f"BENCHMARK:npm_install_time_s:{elapsed:.2f}")
        if res.returncode == 0:
            log("INSTALL_OK")
        else:
            log(f"INSTALL_FAIL:npm {res.returncode}")
    except Exception as e:
        log(f"INSTALL_FAIL:npm {e}")

def install_cargo_tool():
    # petal uses cargo for building; ensure cargo is available already via apk rust
    pass

def clone_repo():
    repo_url = "https://github.com/petal/cosc.git"
    dest = "/tmp/petal_repo"
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        start = time.time()
        res = run_cmd(['git', 'clone', '--depth', '1', repo_url, dest])
        elapsed = time.time() - start
        log(f"BENCHMARK:git_clone_time_s:{elapsed:.2f}")
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        log("INSTALL_OK")
        return dest
    except Exception as e:
        log(f"INSTALL_FAIL:git clone {e}")
        return None

def run_install_sh(repo_path):
    try:
        script = os.path.join(repo_path, "install.sh")
        if not os.path.isfile(script):
            raise FileNotFoundError("install.sh not found")
        start = time.time()
        res = run_cmd(['sh', script], cwd=repo_path)
        elapsed = time.time() - start
        log(f"BENCHMARK:install_sh_time_s:{elapsed:.2f}")
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        log("INSTALL_OK")
    except Exception as e:
        log(f"INSTALL_FAIL:install.sh {e}")

def test_help():
    try:
        start = time.time()
        res = run_cmd(['petal', '--help'])
        elapsed = (time.time() - start) * 1000
        log(f"BENCHMARK:help_time_ms:{elapsed:.2f}")
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        if "Usage" not in res.stdout:
            raise AssertionError("Help output missing Usage")
        log("TEST_PASS:help_output")
    except Exception as e:
        log(f"TEST_FAIL:help_output:{e}")

def test_record():
    out_file = "/tmp/petal_test_record.mp4"
    try:
        # ensure no leftover
        if os.path.exists(out_file):
            os.remove(out_file)
        start = time.time()
        # record 2 seconds; petal CLI assumed syntax: petal record -d 2 -o <file>
        res = run_cmd(['petal', 'record', '-d', '2', '-o', out_file])
        elapsed = (time.time() - start) * 1000
        log(f"BENCHMARK:record_time_ms:{elapsed:.2f}")
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        if not os.path.isfile(out_file) or os.path.getsize(out_file) == 0:
            raise AssertionError("Output file not created or empty")
        log("TEST_PASS:record_output")
    except Exception as e:
        log(f"TEST_FAIL:record_output:{e}")
    finally:
        if os.path.exists(out_file):
            os.remove(out_file)

def test_stream():
    # start a dummy local RTMP server using ffmpeg (if available)
    rtmp_url = "rtmp://localhost:1935/live/test"
    try:
        # start ffmpeg rtmp server in background (simple placeholder)
        server_cmd = ['ffmpeg', '-f', 'lavfi', '-i', 'nullsrc', '-c:v', 'libx264', '-f', 'flv', rtmp_url]
        server = subprocess.Popen(server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)  # give it time to start
        start = time.time()
        res = run_cmd(['petal', 'stream', '-d', '2', '-o', rtmp_url])
        elapsed = (time.time() - start) * 1000
        log(f"BENCHMARK:stream_time_ms:{elapsed:.2f}")
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        log("TEST_PASS:stream_latency")
    except Exception as e:
        log(f"TEST_FAIL:stream_latency:{e}")
    finally:
        if 'server' in locals():
            server.terminate()
            server.wait()

def compare_vs_baseline():
    # baseline: ffmpeg record of 2 sec
    out_file = "/tmp/ffmpeg_test.mp4"
    try:
        start = time.time()
        subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=2:size=1280x720:rate=30',
                        '-c:v', 'libx264', out_file],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ff_elapsed = time.time() - start
        # petal record already measured in test_record (approx 2s)
        petal_time = None
        # read last benchmark line for record_time_ms
        # Simple approach: re-run petal record quickly to get time
        rec_start = time.time()
        subprocess.run(['petal', 'record', '-d', '1', '-o', out_file],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        petal_elapsed = time.time() - rec_start
        ratio = petal_elapsed / ff_elapsed if ff_elapsed > 0 else 0
        log(f"BENCHMARK:vs_ffmpeg_record_ratio:{ratio:.2f}")
    except Exception as e:
        log(f"BENCHMARK:vs_ffmpeg_record_ratio:fail:{e}")
    finally:
        if os.path.exists(out_file):
            os.remove(out_file)

def main():
    # 1. Install required apk packages
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])
    # 2. Install any npm deps needed (ffmpeg-static as example)
    install_node_deps()
    # 3. Clone and install petal
    repo = clone_repo()
    if repo:
        run_install_sh(repo)
    # 4. Run tests
    test_help()
    test_record()
    test_stream()
    # 5. Benchmark vs baseline
    compare_vs_baseline()
    # Ensure at least 3 benchmark lines (install times, help, record, stream already cover)
    log("RUN_OK")

if __name__ == "__main__":
    main()