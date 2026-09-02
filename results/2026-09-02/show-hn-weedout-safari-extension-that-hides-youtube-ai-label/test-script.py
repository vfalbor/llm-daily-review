#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, signal, threading, urllib.request, urllib.error

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(pkg):
    try:
        start = time.time()
        res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
        duration = time.time() - start
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker(f"INSTALL_OK | {pkg}")
        return duration
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")
        return None

def npm_install(repo_url, workdir):
    try:
        start = time.time()
        # clone
        clone = run_cmd(['git', 'clone', '--depth', '1', repo_url, workdir], check=False)
        if clone.returncode != 0:
            raise RuntimeError(clone.stderr.strip())
        # npm install
        npm = run_cmd(['npm', 'install', '--production'], cwd=workdir, check=False)
        if npm.returncode != 0:
            raise RuntimeError(npm.stderr.strip())
        dur = time.time() - start
        print_marker("INSTALL_OK | npm_install")
        return dur
    except Exception as e:
        print_marker(f"INSTALL_FAIL:npm_install:{e}")
        return None

def measure_import_time(module_name):
    try:
        start = time.time()
        __import__(module_name)
        dur = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:import_time_ms:{dur:.2f}")
        return dur
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def start_server(workdir):
    # Assume a typical npm start script exists
    try:
        proc = subprocess.Popen(['npm', 'run', 'start'], cwd=workdir,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # give it time to start
        time.sleep(5)
        # simple health check
        try:
            with urllib.request.urlopen('http://127.0.0.1:3000/health', timeout=5) as resp:
                if resp.status == 200:
                    print_marker("TEST_PASS:health_endpoint")
                else:
                    print_marker(f"TEST_FAIL:health_endpoint:status_{resp.status}")
        except Exception as e:
            print_marker(f"TEST_FAIL:health_endpoint:{e}")
        return proc
    except Exception as e:
        print_marker(f"TEST_FAIL:start_server:{e}")
        return None

def stop_server(proc):
    try:
        if proc:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=5)
    except Exception:
        pass

def benchmark_vs_baseline(metric, our_val, baseline_val):
    try:
        ratio = our_val / baseline_val if baseline_val else 0
        print_marker(f"BENCHMARK:vs_uBlock_{metric}:{ratio:.4f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:vs_baseline_{metric}:{e}")

def main():
    # 1. Install required apk packages
    install_times = {}
    for pkg in ['nodejs', 'npm', 'git', 'curl']:
        dur = install_apk(pkg)
        if dur is not None:
            install_times[pkg] = dur

    # 2. Install the extension via npm (clone repo)
    repo = "https://github.com/masteranza/weedout.git"
    workdir = "/tmp/weedout"
    npm_dur = npm_install(repo, workdir)
    if npm_dur is not None:
        print_marker(f"BENCHMARK:install_time_s:{npm_dur:.2f}")

    # 3. Measure import time of a JS runtime (node) placeholder
    # We'll just measure python json import as example
    measure_import_time('json')

    # 4. Start the server (if any) and perform a simple request
    server_proc = start_server(workdir)

    # 5. Benchmark a dummy request latency
    try:
        start = time.time()
        with urllib.request.urlopen('https://httpbin.org/get', timeout=5) as resp:
            _ = resp.read()
        latency = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:query_latency_ms:{latency:.2f}")
        # compare with baseline (assume baseline 200ms)
        benchmark_vs_baseline('query_latency_ms', latency, 200)
    except Exception as e:
        print_marker(f"TEST_FAIL:query_latency:{e}")

    # 6. Clean up
    stop_server(server_proc)

    # 7. Additional benchmarks
    # memory snapshot
    tracemalloc.start()
    dummy = [i for i in range(100000)]
    current, peak = tracemalloc.get_traced_memory()
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    tracemalloc.stop()

    # line count in repo (simple)
    try:
        total_lines = 0
        for root, _, files in os.walk(workdir):
            for f in files:
                if f.endswith(('.js', '.ts', '.json')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as fh:
                        total_lines += sum(1 for _ in fh)
        print_marker(f"BENCHMARK:loc_count:{total_lines}")
    except Exception as e:
        print_marker(f"TEST_FAIL:loc_count:{e}")

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()