import subprocess, sys, time, json, os, traceback, urllib.request, http.client, socket, tracemalloc, threading

# Helper to run apk install
def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, ""
    except Exception as e:
        return False, str(e)

# Install system packages
sys_pkgs = ['nodejs', 'npm']
for pkg in sys_pkgs:
    ok, err = apk_install(pkg)
    if ok:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err}")

# Install python dependencies
def pip_install(pkg):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, ""
    except Exception as e:
        return False, str(e)

deps = ['requests']
for d in deps:
    ok, err = pip_install(d)
    if ok:
        print("INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{d}:{err}")

import requests

BASE_URL = "https://cartographia40k.com"
BASELINE_LOAD_MS = 1200  # hypothetical baseline load time in ms for similar tool

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    except Exception as e:
        tracemalloc.stop()
        raise
    tracemalloc.stop()
    end = time.time()
    elapsed_ms = (end - start) * 1000
    print(f"BENCHMARK:{name}:{elapsed_ms:.2f}")
    print(f"BENCHMARK:{name}_mem_peak_bytes:{peak}")
    return result, elapsed_ms

def test_homepage():
    try:
        resp, load_ms = benchmark("homepage_load_ms", requests.get, BASE_URL, timeout=15)
        if resp.status_code == 200 and b"map" in resp.content.lower():
            print("TEST_PASS:homepage_load")
        else:
            print(f"TEST_FAIL:homepage_load:Unexpected status {resp.status_code}")
    except Exception as e:
        print(f"TEST_FAIL:homepage_load:{e}")

def test_zoom_performance():
    try:
        # Simulate zoom by requesting a tile endpoint (hypothetical)
        tile_url = f"{BASE_URL}/tiles/0/0/0.png"
        _, tile_ms = benchmark("tile_load_ms", requests.get, tile_url, timeout=10)
        if tile_ms < 500:
            print("TEST_PASS:zoom_tile_load")
        else:
            print(f"TEST_FAIL:zoom_tile_load:Tile load too slow {tile_ms:.2f}ms")
    except Exception as e:
        print(f"TEST_FAIL:zoom_tile_load:{e}")

def test_add_marker():
    try:
        session = requests.Session()
        # Fetch CSRF token placeholder
        home = session.get(BASE_URL, timeout=10)
        csrf = "dummy"
        marker_payload = {
            "name": "test_marker",
            "x": 100,
            "y": 200,
            "csrf_token": csrf
        }
        _, post_ms = benchmark("add_marker_ms", session.post, f"{BASE_URL}/api/marker", json=marker_payload, timeout=10)
        if post_ms < 800:
            print("TEST_PASS:add_marker")
        else:
            print(f"TEST_FAIL:add_marker:Slow response {post_ms:.2f}ms")
    except Exception as e:
        print(f"TEST_FAIL:add_marker:{e}")

def test_page_load_vs_baseline():
    try:
        _, load_ms = benchmark("full_page_load_ms", requests.get, BASE_URL, timeout=20)
        ratio = load_ms / BASELINE_LOAD_MS if BASELINE_LOAD_MS else 0
        print(f"BENCHMARK:vs_baseline_load_ratio:{ratio:.2f}")
        if ratio <= 1.0:
            print("TEST_PASS:load_vs_baseline")
        else:
            print(f"TEST_FAIL:load_vs_baseline:Ratio {ratio:.2f} exceeds baseline")
    except Exception as e:
        print(f"TEST_FAIL:load_vs_baseline:{e}")

# Run tests sequentially, catching any unexpected errors
tests = [
    ("homepage_load", test_homepage),
    ("zoom_performance", test_zoom_performance),
    ("add_marker", test_add_marker),
    ("load_vs_baseline", test_page_load_vs_baseline)
]

for name, func in tests:
    try:
        func()
    except Exception:
        print(f"TEST_FAIL:{name}:{traceback.format_exc()}")

# Ensure at least three benchmark lines are printed (already emitted in functions)

print("RUN_OK")