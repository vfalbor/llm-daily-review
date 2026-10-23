#!/usr/bin/env python3
import subprocess, sys, time, os, json, shlex, traceback, urllib.request, threading, signal, tracemalloc

def print_marker(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def safe_subprocess(cmd, check=False):
    try:
        res = run_cmd(cmd, check=check)
        return res
    except Exception as e:
        return None

def install_apk_packages():
    start = time.time()
    pkgs = ["nodejs", "npm", "git", "curl"]
    for pkg in pkgs:
        safe_subprocess(['apk', 'add', '--no-cache', pkg])
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")

def clone_repo():
    start = time.time()
    repo_url = "https://github.com/maxilevi/project-hedra.git"
    dest = "/tmp/project-hedra"
    if os.path.isdir(dest):
        safe_subprocess(['rm', '-rf', dest])
    res = safe_subprocess(['git', 'clone', '--depth', '1', repo_url, dest])
    if res is None or res.returncode != 0:
        print_marker(f"TEST_FAIL:clone_repo:Git clone failed")
        return None
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:clone_time_s:{elapsed:.2f}")
    return dest

def try_npm_install(repo_path):
    start = time.time()
    npm_cmd = ['npm', 'install', '--silent']
    res = safe_subprocess(npm_cmd, cwd=repo_path)
    if res is None or res.returncode != 0:
        print_marker(f"TEST_FAIL:npm_install:NPM install failed")
        return False
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:npm_install_time_s:{elapsed:.2f}")
    return True

def start_server(repo_path):
    # Guess a start script; many Unity projects have no server.
    # We'll try `npm run start` or `node server.js`
    start_cmds = [
        ['npm', 'run', 'start', '--silent'],
        ['node', 'server.js']
    ]
    for cmd in start_cmds:
        try:
            proc = subprocess.Popen(cmd, cwd=repo_path,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    preexec_fn=os.setsid)
            # give it a moment to start
            time.sleep(3)
            # check if process is still alive
            if proc.poll() is None:
                print_marker("TEST_PASS:start_server")
                return proc
        except Exception:
            continue
    print_marker("TEST_FAIL:start_server:No recognizable start command")
    return None

def health_check(url="http://127.0.0.1:3000/health"):
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = resp.read()
            latency = (time.time() - start) * 1000
            print_marker(f"BENCHMARK:health_check_latency_ms:{latency:.2f}")
            print_marker("TEST_PASS:health_check")
            return True
    except Exception as e:
        latency = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:health_check_latency_ms:{latency:.2f}")
        print_marker(f"TEST_FAIL:health_check:{e.__class__.__name__}")
        return False

def stop_process(proc):
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        pass

def benchmark_vs_baseline(metric, value, baseline_value):
    try:
        ratio = float(value) / float(baseline_value)
        print_marker(f"BENCHMARK:vs_unreal_{metric}:{ratio:.2f}")
    except Exception:
        pass

def main():
    tracemalloc.start()
    try:
        install_apk_packages()
        repo_path = clone_repo()
        if not repo_path:
            raise RuntimeError("Clone failed")
        npm_ok = try_npm_install(repo_path)
        server_proc = None
        if npm_ok:
            server_proc = start_server(repo_path)
        if server_proc:
            health_ok = health_check()
        else:
            health_ok = False

        # Example benchmark: memory usage after start
        current, peak = tracemalloc.get_traced_memory()
        print_marker(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
        print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

        # Compare with baseline (dummy numbers)
        benchmark_vs_baseline("memory_current_kb", current/1024, 50000)  # assume 50MB baseline
        benchmark_vs_baseline("memory_peak_kb", peak/1024, 80000)      # assume 80MB baseline

    except Exception as e:
        tb = traceback.format_exc().splitlines()[-1]
        print_marker(f"TEST_FAIL:main:{tb}")
    finally:
        if 'server_proc' in locals() and server_proc:
            stop_process(server_proc)
        print_marker("RUN_OK")

if __name__ == "__main__":
    main()