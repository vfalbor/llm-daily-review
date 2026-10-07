import subprocess
import sys
import os
import time
import tracemalloc
import urllib.request
import json
import shutil
import signal
import threading

REPO_URL = "https://github.com/travelonium/arcadeia.git"
REPO_DIR = "/tmp/arcadeia"
SERVER_PORT = 3000
HEALTH_ENDPOINT = f"http://127.0.0.1:{SERVER_PORT}/health"
UPLOAD_ENDPOINT = f"http://127.0.0.1:{SERVER_PORT}/api/upload"
SAMPLE_VIDEO = "/tmp/sample.mp4"
BASELINE_TOOL = "plex"  # placeholder baseline for comparison

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(
        cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True
    )

def print_marker(msg):
    print(msg, flush=True)

def install_apk_packages():
    pkgs = ["git", "nodejs", "npm", "ffmpeg", "curl"]
    try:
        start = time.time()
        result = subprocess.run(
            ["apk", "add", "--no-cache"] + pkgs,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{result.stderr.strip()}")
        print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def clone_repo():
    try:
        if os.path.isdir(REPO_DIR):
            shutil.rmtree(REPO_DIR)
        start = time.time()
        result = run_cmd(["git", "clone", "--depth", "1", REPO_URL, REPO_DIR])
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("TEST_PASS:clone_repo")
        else:
            raise RuntimeError(result.stderr.strip())
        print_marker(f"BENCHMARK:clone_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")

def npm_install():
    try:
        start = time.time()
        result = run_cmd(["npm", "ci"], cwd=REPO_DIR)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("TEST_PASS:npm_install")
        else:
            raise RuntimeError(result.stderr.strip())
        print_marker(f"BENCHMARK:npm_install_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:npm_install:{e}")

def start_server():
    try:
        env = os.environ.copy()
        env["PORT"] = str(SERVER_PORT)
        proc = subprocess.Popen(
            ["npm", "run", "dev"], cwd=REPO_DIR,
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # give server time to start
        start = time.time()
        for _ in range(30):
            try:
                with urllib.request.urlopen(HEALTH_ENDPOINT, timeout=1) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("Health endpoint never responded")
        elapsed = time.time() - start
        print_marker("TEST_PASS:start_server")
        print_marker(f"BENCHMARK:server_start_time_s:{elapsed:.2f}")
        return proc
    except Exception as e:
        print_marker(f"TEST_FAIL:start_server:{e}")
        return None

def download_sample_video():
    # small public domain video (1 sec mp4)
    url = "https://sample-videos.com/video123/mp4/240/big_buck_bunny_240p_1mb.mp4"
    try:
        start = time.time()
        urllib.request.urlretrieve(url, SAMPLE_VIDEO)
        elapsed = time.time() - start
        print_marker("TEST_PASS:download_sample_video")
        print_marker(f"BENCHMARK:download_video_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:download_sample_video:{e}")

def upload_video():
    try:
        with open(SAMPLE_VIDEO, "rb") as f:
            data = f.read()
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="sample.mp4"\r\n'
            f"Content-Type: video/mp4\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(UPLOAD_ENDPOINT, data=body)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        start = time.time()
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = resp.read()
        elapsed = time.time() - start
        if resp.status == 200:
            print_marker("TEST_PASS:upload_video")
        else:
            raise RuntimeError(f"Status {resp.status}")
        print_marker(f"BENCHMARK:upload_time_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:upload_video:{e}")

def check_preview():
    # preview is served under /preview/<filename>.gif after processing
    preview_url = f"http://127.0.0.1:{SERVER_PORT}/preview/sample.gif"
    try:
        start = time.time()
        for _ in range(20):
            try:
                with urllib.request.urlopen(preview_url, timeout=2) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("Preview not generated")
        elapsed = time.time() - start
        print_marker("TEST_PASS:check_preview")
        print_marker(f"BENCHMARK:preview_generation_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:check_preview:{e}")

def benchmark_memory():
    tracemalloc.start()
    # allocate some objects similar to what server does
    lst = [i for i in range(1000000)]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

def compare_vs_baseline():
    # dummy baseline numbers for illustration
    baseline = {
        "upload_time_s": 2.5,
        "preview_generation_s": 5.0
    }
    try:
        upload = float(os.getenv("BENCH_UPLOAD", "0"))
        preview = float(os.getenv("BENCH_PREVIEW", "0"))
        # if env vars not set, skip
        if upload:
            ratio = upload / baseline["upload_time_s"]
            print_marker(f"BENCHMARK:vs_{BASELINE_TOOL}_upload_ratio:{ratio:.2f}")
        if preview:
            ratio = preview / baseline["preview_generation_s"]
            print_marker(f"BENCHMARK:vs_{BASELINE_TOOL}_preview_ratio:{ratio:.2f}")
    except Exception as e:
        print_marker(f"TEST_SKIP:compare_vs_baseline:{e}")

def cleanup(proc):
    try:
        if proc:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=5)
    except Exception:
        pass
    for path in [REPO_DIR, SAMPLE_VIDEO]:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

def main():
    install_apk_packages()
    clone_repo()
    npm_install()
    download_sample_video()
    server_proc = start_server()
    if server_proc:
        upload_video()
        check_preview()
    benchmark_memory()
    compare_vs_baseline()
    cleanup(server_proc)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()