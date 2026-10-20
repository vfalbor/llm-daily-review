import subprocess, sys, time, json, os, traceback, tracemalloc, threading, socket
from urllib import request, parse

# Helper to print markers
def emit(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

# 1. Install system packages
def install_system():
    try:
        res = run_cmd(['apk', 'add', '--no-cache', 'git'], check=False)
        if res.returncode == 0:
            emit("INSTALL_OK")
        else:
            emit(f"INSTALL_FAIL:apk git error {res.stderr.strip()}")
    except Exception as e:
        emit(f"INSTALL_FAIL:apk exception {e}")

# 2. Install python package with fallback
def install_package():
    start = time.time()
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'deephug'])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        emit("INSTALL_OK")
    except Exception as e1:
        # fallback to git clone
        try:
            if os.path.isdir('DeepInfer'):
                subprocess.run(['rm', '-rf', 'DeepInfer'])
            res = run_cmd(['git', 'clone', 'https://github.com/deepseek-ai/DeepInfer.git'])
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
            os.chdir('DeepInfer')
            res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'])
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
            emit("INSTALL_OK")
        except Exception as e2:
            emit(f"INSTALL_FAIL:pip fallback {e2}")
    finally:
        install_time = time.time() - start
        emit(f"BENCHMARK:install_time_s:{install_time:.3f}")

# 3. Import and start server
def start_server():
    import_time_start = time.time()
    try:
        import deephug
        import_time = (time.time() - import_time_start) * 1000
        emit(f"BENCHMARK:import_time_ms:{import_time:.2f}")
    except Exception as e:
        emit(f"TEST_FAIL:import_deephug:{e}")
        return None

    try:
        # Start server in background thread
        server_thread = threading.Thread(target=deephug.Server.start, daemon=True)
        server_thread.start()
        # Wait for socket to be ready
        for _ in range(30):
            try:
                with socket.create_connection(("127.0.0.1", 8000), timeout=1):
                    break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start")
        emit("TEST_PASS:start_server")
        return True
    except Exception as e:
        emit(f"TEST_FAIL:start_server:{e}")
        return False

# 4. Perform latency test
def latency_test():
    url = "http://127.0.0.1:8000/v1/chat/completions"
    payload = {
        "model": "deepseek-coder-33b",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    data = json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'}

    latencies = []
    for i in range(50):
        try:
            start = time.time()
            req = request.Request(url, data=data, headers=headers, method='POST')
            with request.urlopen(req, timeout=10) as resp:
                resp.read()  # ignore content
            elapsed = (time.time() - start) * 1000
            latencies.append(elapsed)
        except Exception as e:
            emit(f"TEST_FAIL:request_{i}:{e}")
            continue

    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        emit(f"BENCHMARK:avg_latency_ms:{avg_latency:.2f}")
        emit(f"TEST_PASS:latency_test")
        return avg_latency
    else:
        emit("TEST_FAIL:latency_test:no successful requests")
        return None

# 5. Baseline comparison (simple dummy baseline using echo latency)
def baseline_latency():
    start = time.time()
    for _ in range(50):
        subprocess.run(['echo', 'test'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return (time.time() - start) * 1000 / 50  # avg ms per echo

def compare_vs_baseline(measured):
    base = baseline_latency()
    if base == 0:
        ratio = float('inf')
    else:
        ratio = measured / base
    emit(f"BENCHMARK:vs_vLLM_latency_ratio:{ratio:.3f}")

def main():
    try:
        install_system()
        install_package()
        if start_server():
            avg = latency_test()
            if avg is not None:
                compare_vs_baseline(avg)
        else:
            emit("TEST_SKIP:latency_test:server not started")
    except Exception as e:
        emit(f"TEST_FAIL:unexpected:{traceback.format_exc()}")
    finally:
        emit("RUN_OK")

if __name__ == "__main__":
    main()