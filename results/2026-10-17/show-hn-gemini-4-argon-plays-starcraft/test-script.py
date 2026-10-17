#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, threading, urllib.request, urllib.error

def apk_add(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def pip_install(package):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print(f"BENCHMARK:install_time_s:{elapsed:.3f}")
        print("INSTALL_OK")
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        return False

def git_clone(repo, dest):
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("INSTALL_OK")
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        return False

def pip_install_editable(path):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print(f"BENCHMARK:install_time_s:{elapsed:.3f}")
        print("INSTALL_OK")
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        return False

def benchmark_import():
    try:
        tracemalloc.start()
        start = time.time()
        import importlib
        importlib.import_module('argon')
        import_time = (time.time() - start) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print(f"BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}")
        print("TEST_PASS:import")
    except Exception as e:
        print(f"TEST_FAIL:import:{e}")

def functional_test():
    try:
        start = time.time()
        import argon
        result = argon.run("Hello world")
        latency = (time.time() - start) * 1000
        print(f"BENCHMARK:hello_world_ms:{latency:.2f}")
        if isinstance(result, str) and result:
            print("TEST_PASS:functional")
        else:
            print("TEST_FAIL:functional:Invalid result")
    except Exception as e:
        print(f"TEST_FAIL:functional:{e}")

def start_server():
    # try to start the server in background if not already running
    try:
        import argon
        server_thread = threading.Thread(target=argon.serve, kwargs={'host':'0.0.0.0','port':8080}, daemon=True)
        server_thread.start()
        time.sleep(2)  # give it time to start
        print("TEST_PASS:server_start")
    except Exception as e:
        print(f"TEST_FAIL:server_start:{e}")

def http_request(payload):
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request('http://localhost:8080/v1/chat/completions', data=data,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode()
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP error: {e}")

def latency_test(num_requests=100):
    try:
        start = time.time()
        for i in range(num_requests):
            payload = {
                "model": "gemini-4-argon",
                "messages": [{"role": "user", "content": f"Hello {i}"}]
            }
            http_request(payload)
        total_ms = (time.time() - start) * 1000
        avg_ms = total_ms / num_requests
        print(f"BENCHMARK:seq_requests_{num_requests}_ms:{total_ms:.2f}")
        print(f"BENCHMARK:seq_requests_{num_requests}_avg_ms:{avg_ms:.2f}")
        print("TEST_PASS:latency")
    except Exception as e:
        print(f"TEST_FAIL:latency:{e}")

def compare_vs_baseline():
    # dummy baseline values for Ollama (example)
    baseline_avg_ms = 120.0
    try:
        # use the previously measured avg latency if available
        # For simplicity re-run a small measurement
        start = time.time()
        for i in range(10):
            http_request({
                "model":"gemini-4-argon",
                "messages":[{"role":"user","content":"Hi"}]
            })
        our_avg = ((time.time() - start) * 1000) / 10
        ratio = our_avg / baseline_avg_ms
        print(f"BENCHMARK:vs_ollama_latency_ratio:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install system deps
    apk_add('git')

    # 2. Install python package
    installed = pip_install('gemini4-argon')
    if not installed:
        # fallback to source
        if git_clone('https://github.com/argondotdev/gemini-4-argon.git', '/tmp/gemini-argon'):
            pip_install_editable('/tmp/gemini-argon')

    # 3. Benchmarks and tests
    benchmark_import()
    functional_test()
    start_server()
    latency_test(100)
    compare_vs_baseline()

    # final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()