import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def run_cmd(cmd, description):
    try:
        start = time.time()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        duration = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK | {description}")
            return True, duration, result.stdout
        else:
            reason = result.stderr.strip().splitlines()[-1] if result.stderr else "unknown error"
            print_marker(f"INSTALL_FAIL:{reason}")
            return False, duration, result.stderr
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{str(e)}")
        return False, 0.0, str(e)

def install_system():
    success, dur, _ = run_cmd(['apk','add','--no-cache','git','python3','py3-pip'], "system_packages")
    return success, dur

def pip_install_pkg():
    # try pip install directly from git repo
    repo = "https://github.com/morronel/requests_please.git"
    success, dur, out = run_cmd([sys.executable, "-m", "pip", "install", "git+" + repo], "pip_install_git")
    if success:
        return True, dur
    # fallback: git clone then pip install -e .
    tmp_dir = "/tmp/requests_please"
    if os.path.isdir(tmp_dir):
        subprocess.run(['rm','-rf',tmp_dir])
    success_clone, dur_clone, out_clone = run_cmd(['git','clone',repo,tmp_dir], "git_clone")
    if not success_clone:
        return False, dur + dur_clone
    success_edit, dur_edit, out_edit = run_cmd([sys.executable, "-m", "pip", "install", "-e", tmp_dir], "pip_install_editable")
    return success_edit, dur + dur_clone + dur_edit

def benchmark_import():
    tracemalloc.start()
    start = time.time()
    try:
        import requests_please
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        mem_kb = peak / 1024
        print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_mem_kb:{mem_kb:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import:{str(e)}")
        return False
    finally:
        tracemalloc.stop()

def test_mocked_request():
    import requests
    from requests_please import RequestsPlease
    rp = RequestsPlease()
    # define a mock endpoint
    url = "https://api.example.com/data"
    expected_json = {"status":"ok","value":42}
    rp.mock(url, json=expected_json, status=200)

    start = time.time()
    try:
        resp = requests.get(url)
        latency = (time.time() - start) * 1000  # ms
        if resp.json() != expected_json:
            raise AssertionError("Mocked response mismatch")
        print_marker(f"TEST_PASS:mocked_request")
        print_marker(f"BENCHMARK:mocked_request_latency_ms:{latency:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:mocked_request:{str(e)}")
        return False

def test_header_query_forward():
    import requests
    from requests_please import RequestsPlease
    rp = RequestsPlease()
    url = "https://api.example.com/echo"
    rp.mock(url, json={"ok":True})

    headers = {"X-Custom":"HeaderValue"}
    params = {"q":"test"}
    try:
        resp = requests.get(url, headers=headers, params=params)
        # Verify that the mock recorded the request correctly
        recorded = rp.last_request(url)
        if recorded is None:
            raise AssertionError("No request recorded")
        if recorded.get("headers",{}).get("X-Custom") != "HeaderValue":
            raise AssertionError("Header not forwarded")
        if recorded.get("params",{}) != params:
            raise AssertionError("Query params not forwarded")
        print_marker("TEST_PASS:header_query_forward")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:header_query_forward:{str(e)}")
        return False

def benchmark_baseline():
    # Compare with requests-mock (baseline)
    try:
        import requests_mock
        import requests
        with requests_mock.Mocker() as m:
            url = "https://api.example.com/baseline"
            m.get(url, json={"x":1})
            start = time.time()
            r = requests.get(url)
            latency = (time.time() - start) * 1000
        # baseline latency
        return latency
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_setup:{str(e)}")
        return None

def main():
    # 1. System packages
    sys_success, sys_time = install_system()
    print_marker(f"BENCHMARK:system_install_time_s:{sys_time:.2f}")

    # 2. Install package
    pkg_success, pkg_time = pip_install_pkg()
    print_marker(f"BENCHMARK:package_install_time_s:{pkg_time:.2f}")

    # 3. Import benchmark
    if pkg_success:
        benchmark_import()
    else:
        print_marker("TEST_SKIP:import:package not installed")

    # 4. Functional tests
    try:
        test_mocked_request()
    except Exception:
        print_marker(f"TEST_FAIL:mocked_request:{traceback.format_exc()}")

    try:
        test_header_query_forward()
    except Exception:
        print_marker(f"TEST_FAIL:header_query_forward:{traceback.format_exc()}")

    # 5. Compare against baseline
    baseline_latency = benchmark_baseline()
    if baseline_latency:
        # run our mocked request again to get our latency
        import time, requests
        from requests_please import RequestsPlease
        rp = RequestsPlease()
        url = "https://api.example.com/compare"
        rp.mock(url, json={"ok":True})
        start = time.time()
        requests.get(url)
        our_latency = (time.time() - start) * 1000
        ratio = our_latency / baseline_latency if baseline_latency else 0
        print_marker(f"BENCHMARK:vs_requests_mock_latency_ratio:{ratio:.2f}")

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()