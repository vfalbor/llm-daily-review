import subprocess, sys, os, time, json, traceback, http.client, urllib.request, urllib.error, urllib.parse, socket, threading, tracemalloc, shlex
from pathlib import Path

def log(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None, timeout=300):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        duration = time.time() - start
        return result, duration
    except Exception as e:
        return e, None

def install_apk():
    pkgs = ["nodejs", "npm", "git"]
    result, _ = run_cmd(["apk", "add", "--no-cache"] + pkgs, check=False)
    if isinstance(result, subprocess.CalledProcessError) or isinstance(result, Exception):
        log(f"INSTALL_FAIL:apk_add:{getattr(result, 'stderr', str(result)).strip()}")
        return False
    log("INSTALL_OK")
    return True

def clone_repo():
    repo_url = "https://github.com/rupertlinacre/buslens.git"
    dest = Path("/tmp/buslens")
    if dest.exists():
        subprocess.run(["rm", "-rf", str(dest)])
    result, dur = run_cmd(["git", "clone", "--depth", "1", repo_url, str(dest)])
    if isinstance(result, Exception) or result.returncode != 0:
        log(f"TEST_FAIL:clone_repo:{getattr(result, 'stderr', str(result)).strip()}")
        return None, None
    log(f"TEST_PASS:clone_repo")
    log(f"BENCHMARK:clone_time_s:{dur:.3f}")
    return dest, dur

def npm_install(repo_path):
    start = time.time()
    result, dur = run_cmd(["npm", "install"], cwd=repo_path)
    if isinstance(result, Exception) or result.returncode != 0:
        log(f"TEST_FAIL:npm_install:{getattr(result, 'stderr', str(result)).strip()}")
        return False, dur
    log("TEST_PASS:npm_install")
    log(f"BENCHMARK:npm_install_time_s:{dur:.3f}")
    return True, dur

def start_server(repo_path):
    env = os.environ.copy()
    env["PORT"] = "3000"
    proc = subprocess.Popen(["npm", "run", "dev"], cwd=repo_path, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # give it time to start
    start = time.time()
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:3000", timeout=2) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(1)
    else:
        log("TEST_FAIL:start_server:timeout")
        proc.terminate()
        return None, time.time() - start
    log("TEST_PASS:start_server")
    log(f"BENCHMARK:server_startup_s:{time.time() - start:.3f}")
    return proc, time.time() - start

def stop_server(proc):
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

def check_homepage():
    try:
        start = time.time()
        with urllib.request.urlopen("http://127.0.0.1:3000", timeout=5) as resp:
            data = resp.read()
        dur = time.time() - start
        if resp.status == 200 and b"Buslens" in data:
            log("TEST_PASS:homepage_load")
        else:
            log("TEST_FAIL:homepage_load:unexpected_content")
        log(f"BENCHMARK:homepage_load_ms:{dur*1000:.2f}")
    except Exception as e:
        log(f"TEST_FAIL:homepage_load:{e}")
        log(f"BENCHMARK:homepage_load_ms:-1")

def run_npm_tests(repo_path):
    result, dur = run_cmd(["npm", "test"], cwd=repo_path)
    if isinstance(result, Exception) or result.returncode != 0:
        log(f"TEST_FAIL:npm_test:{getattr(result, 'stderr', str(result)).strip()}")
    else:
        log("TEST_PASS:npm_test")
    log(f"BENCHMARK:npm_test_time_s:{dur:.3f}")

def api_benchmark(repo_path):
    # mock API key via env if needed
    os.environ["BUSLENS_API_KEY"] = "FAKE_KEY"
    endpoint = "http://127.0.0.1:3000/api/schedule?route=10"
    try:
        start = time.time()
        with urllib.request.urlopen(endpoint, timeout=5) as resp:
            _ = resp.read()
        dur = time.time() - start
        log(f"BENCHMARK:api_schedule_latency_ms:{dur*1000:.2f}")
        # compare with baseline (assume baseline 200ms)
        baseline = 200.0
        ratio = (dur*1000) / baseline
        log(f"BENCHMARK:vs_transit_api_latency_ratio:{ratio:.3f}")
    except urllib.error.HTTPError as e:
        log(f"TEST_FAIL:api_schedule:{e.code}")
    except Exception as e:
        log(f"TEST_FAIL:api_schedule:{e}")

def main():
    tracemalloc.start()
    if not install_apk():
        pass
    repo_path, _ = clone_repo()
    if not repo_path:
        log("RUN_OK")
        return
    ok, _ = npm_install(repo_path)
    if not ok:
        log("RUN_OK")
        return
    server_proc, _ = start_server(repo_path)
    if not server_proc:
        log("RUN_OK")
        return
    try:
        check_homepage()
        run_npm_tests(repo_path)
        api_benchmark(repo_path)
    finally:
        stop_server(server_proc)
    current, peak = tracemalloc.get_traced_memory()
    log(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
    log(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    log("RUN_OK")

if __name__ == "__main__":
    main()