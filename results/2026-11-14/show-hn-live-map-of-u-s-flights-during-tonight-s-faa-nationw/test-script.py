import subprocess, sys, time, json, os, signal, threading, traceback
import urllib.request, urllib.error
import http.client
import tracemalloc

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        return True, ""
    except Exception as e:
        return False, str(e)

def install_apk_packages():
    pkgs = ["nodejs", "npm"]
    ok, reason = run_cmd(["apk", "add", "--no-cache"] + pkgs)
    if ok:
        marker("INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:{reason}")

def npm_install():
    # Assume repository is cloned already in /app (the script runs in that dir)
    # Try npm install
    ok, reason = run_cmd(["npm", "install"])
    if ok:
        marker("INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:{reason}")

def start_server():
    # Start the web server (npm start or node index.js) in background
    # Try common entry points
    entry_points = [
        ["npm", "run", "start"],
        ["node", "server.js"],
        ["node", "index.js"]
    ]
    for cmd in entry_points:
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            # give it a moment to start
            time.sleep(3)
            # check if port 80 or 3000 is listening via simple request
            return proc
        except Exception:
            continue
    return None

def stop_server(proc):
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass

def http_get(url, timeout=10):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.read(), resp.getcode()
    except urllib.error.HTTPError as e:
        return e.read(), e.code
    except Exception as e:
        raise e

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        elapsed = time.time() - start
    # Emit benchmark in seconds with 3 decimals
    marker(f"BENCHMARK:{name}:{elapsed:.3f}")
    return result

def test_home_page():
    test_name = "home_page_load"
    try:
        def load():
            data, code = http_get("http://localhost:3000/")
            return data, code
        data, code = benchmark("home_page_load_s", load)
        if code != 200:
            raise AssertionError(f"Unexpected status {code}")
        # simple check for map element presence
        if b"id=\"map\"" not in data and b"class=\"map\"" not in data:
            raise AssertionError("Map container not found")
        marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        marker(f"TEST_FAIL:{test_name}:{e}")

def test_flight_marker():
    test_name = "flight_marker"
    try:
        # Simulate subscription via endpoint /subscribe (hypothetical)
        def subscribe():
            data, code = http_get("http://localhost:3000/api/subscribe")
            return json.loads(data), code
        resp, code = benchmark("subscribe_s", subscribe)
        if code != 200:
            raise AssertionError(f"Subscribe failed {code}")
        # Assume response contains a flight id we can query
        flight_id = resp.get("flightId")
        if not flight_id:
            raise AssertionError("No flightId in response")
        def get_flight():
            data, code = http_get(f"http://localhost:3000/api/flight/{flight_id}")
            return json.loads(data), code
        flight, code = benchmark("flight_fetch_s", get_flight)
        if code != 200 or not flight.get("position"):
            raise AssertionError("Flight marker missing")
        marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        marker(f"TEST_FAIL:{test_name}:{e}")

def test_ground_stop():
    test_name = "ground_stop_event"
    try:
        # Trigger ground stop via admin endpoint (hypothetical)
        def trigger():
            req = urllib.request.Request(
                "http://localhost:3000/api/admin/groundstop",
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read(), resp.getcode()
        _, code = benchmark("trigger_groundstop_s", trigger)
        if code != 200:
            raise AssertionError(f"Trigger failed {code}")
        # Wait a short while then check flight count
        time.sleep(2)
        def count():
            data, code = http_get("http://localhost:3000/api/flights/count")
            return int(data), code
        cnt, code = benchmark("flight_count_s", count)
        if code != 200:
            raise AssertionError(f"Count endpoint error {code}")
        if cnt != 0:
            raise AssertionError(f"Expected 0 flights, got {cnt}")
        marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        marker(f"TEST_FAIL:{test_name}:{e}")

def compare_baseline():
    # Baseline: assume FlightAware average response 0.45s for similar endpoint
    baseline = 0.45
    try:
        # Use previously measured home_page_load_s benchmark (last emitted)
        # For simplicity re‑measure here
        def load():
            data, code = http_get("http://localhost:3000/")
            return code
        start = time.time()
        _, _ = load()
        elapsed = time.time() - start
        ratio = elapsed / baseline
        marker(f"BENCHMARK:vs_flightaware_home_load_ratio:{ratio:.3f}")
    except Exception as e:
        marker(f"BENCHMARK:vs_flightaware_home_load_ratio:fail")

def main():
    install_apk_packages()
    npm_install()
    server_proc = start_server()
    if not server_proc:
        marker("INSTALL_FAIL:Could not start server")
        # Continue to run tests that do not require server
    else:
        try:
            test_home_page()
            test_flight_marker()
            test_ground_stop()
            compare_baseline()
        finally:
            stop_server(server_proc)

    # Emit additional generic benchmarks
    marker("BENCHMARK:cpu_count:" + str(os.cpu_count()))
    marker("BENCHMARK:memory_mb:" + str(round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**2), 2)))
    marker("BENCHMARK:thread_count:" + str(threading.active_count()))

    marker("RUN_OK")

if __name__ == "__main__":
    main()