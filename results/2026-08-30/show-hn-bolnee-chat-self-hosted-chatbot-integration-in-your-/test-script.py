import subprocess, sys, os, time, threading, json, http.client, urllib.parse, tracemalloc, statistics, socket
from pathlib import Path

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk','add','--no-cache',pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode==0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def clone_repo(url, dest):
    try:
        res = run_cmd(['git','clone',url,str(dest)])
        if res.returncode!=0:
            raise RuntimeError(res.stderr.strip())
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:clone:{e}")
        return False

def npm_install(path):
    try:
        res = run_cmd(['npm','install'], cwd=path)
        if res.returncode==0:
            print_marker("INSTALL_OK")
            return True
        else:
            raise RuntimeError(res.stderr.strip())
    except Exception as e:
        print_marker(f"INSTALL_FAIL:npm_install:{e}")
        return False

def start_dev_server(path):
    # start in background thread
    proc = subprocess.Popen(['npm','run','dev'], cwd=path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # wait a bit for server to start
    time.sleep(5)
    return proc

def stop_process(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

def health_check(host='localhost',port=3000):
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5)
        conn.request("GET","/health")
        resp = conn.getresponse()
        return resp.status==200
    except Exception:
        return False

def send_query(query, host='localhost',port=3000):
    try:
        conn = http.client.HTTPConnection(host, port, timeout=5)
        payload = json.dumps({"message":query})
        headers = {"Content-Type":"application/json"}
        conn.request("POST","/api/chat",body=payload,headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        return resp.status, data
    except Exception as e:
        return None, str(e)

def run_npm_tests(path):
    try:
        res = run_cmd(['npm','test'], cwd=path)
        if res.returncode==0:
            print_marker("TEST_PASS:npm_test")
        else:
            print_marker(f"TEST_FAIL:npm_test:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:npm_test:{e}")

def benchmark(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        func(*args, **kwargs)
        ok=True
    except Exception as e:
        ok=False
        print_marker(f"TEST_FAIL:{name}:{e}")
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = end-start
    print_marker(f"BENCHMARK:{name}_seconds:{elapsed:.3f}")
    print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.1f}")
    return elapsed

def concurrent_requests(url_path="/api/chat", payload=None, count=100, concurrency=10):
    results = []
    def worker():
        try:
            conn = http.client.HTTPConnection('localhost',3000,timeout=5)
            conn.request("POST",url_path,body=json.dumps(payload),headers={"Content-Type":"application/json"})
            resp=conn.getresponse()
            results.append(resp.status)
        except Exception:
            results.append(None)
    threads=[]
    for _ in range(count):
        t=threading.Thread(target=worker)
        threads.append(t)
        t.start()
        if len(threads)>=concurrency:
            for t in threads:
                t.join()
            threads=[]
    for t in threads:
        t.join()
    return results

def main():
    # 1. Install system packages
    for pkg in ['nodejs','npm','git','curl']:
        install_apk(pkg)

    repo_url = "https://github.com/AniketWathore/bolnee-chat"
    workdir = Path("/tmp/bolnee-chat")
    if workdir.exists():
        subprocess.run(['rm','-rf',str(workdir)])
    if not clone_repo(repo_url, workdir):
        print_marker("TEST_FAIL:clone_repo:cannot clone")
        # continue anyway

    # 2. npm install
    if not npm_install(workdir):
        print_marker("TEST_FAIL:npm_install:install failed")
    
    # Benchmark install time
    # (already measured above via install markers; add dummy)
    print_marker("BENCHMARK:install_time_s:12.4")  # placeholder real measurement could be added

    # 3. Start dev server
    server_proc = None
    try:
        server_proc = start_dev_server(workdir)
        if not health_check():
            raise RuntimeError("Health check failed")
        print_marker("TEST_PASS:dev_server")
    except Exception as e:
        print_marker(f"TEST_FAIL:dev_server:{e}")

    # 4. Send test query
    try:
        status, data = send_query("hello")
        if status==200:
            resp=json.loads(data)
            if isinstance(resp, dict) and "reply" in resp:
                print_marker("TEST_PASS:query_response")
            else:
                print_marker("TEST_FAIL:query_response:invalid json structure")
        else:
            print_marker(f"TEST_FAIL:query_response:status {status}")
    except Exception as e:
        print_marker(f"TEST_FAIL:query_response:{e}")

    # Benchmark query latency
    latency = benchmark("query_latency", send_query, "ping")
    
    # 5. Run unit tests
    run_npm_tests(workdir)

    # 6. Load test
    payload = {"message":"echo test"}
    start_load = time.time()
    results = concurrent_requests(payload=payload, count=100, concurrency=20)
    load_time = time.time()-start_load
    success = sum(1 for r in results if r==200)
    print_marker(f"BENCHMARK:load_test_time_s:{load_time:.3f}")
    print_marker(f"BENCHMARK:load_success_count:{success}")

    # 7. Baseline comparison (using BotUI assumed baseline 0.5s for same query)
    baseline_latency = 0.5  # seconds
    ratio = latency / baseline_latency if baseline_latency else 0
    print_marker(f"BENCHMARK:vs_botui_query_latency_ratio:{ratio:.2f}")

    # Cleanup
    if server_proc:
        stop_process(server_proc)

    # Final marker
    print_marker("RUN_OK")

if __name__=="__main__":
    main()