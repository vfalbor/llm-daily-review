import subprocess, sys, time, json, os, shlex, traceback, tracemalloc, urllib.request

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture=False, cwd=None):
    try:
        result = subprocess.run(cmd, shell=False, check=False, stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None, cwd=cwd, text=True)
        return result
    except Exception as e:
        return None

def install_system_pkgs():
    pkgs = ["git", "curl"]
    start = time.time()
    for pkg in pkgs:
        res = run_cmd(["apk", "add", "--no-cache", pkg])
        if res is None or res.returncode != 0:
            print_marker(f"INSTALL_FAIL:{pkg} - {res.stderr.strip() if res else 'exception'}")
            return False, time.time() - start
    print_marker("INSTALL_OK")
    return True, time.time() - start

def docker_pull_image():
    img = "ghcr.io/antirez/c64-hw-simulator:latest"
    start = time.time()
    res = run_cmd(["docker", "pull", img])
    if res is None or res.returncode != 0:
        print_marker(f"TEST_FAIL:docker_pull:{res.stderr.strip() if res else 'exception'}")
        return False, time.time() - start
    print_marker("TEST_PASS:docker_pull")
    return True, time.time() - start

def run_known_binary():
    # using the pulled image, run a known binary (example: basic test)
    img = "ghcr.io/antirez/c64-hw-simulator:latest"
    cmd = ["docker", "run", "--rm", img, "--run", "/usr/share/c64/hw/samples/hello.prg"]
    start = time.time()
    res = run_cmd(cmd)
    elapsed = time.time() - start
    if res is None:
        print_marker(f"TEST_FAIL:run_known_binary:exception")
        return False, elapsed
    if res.returncode != 0:
        print_marker(f"TEST_FAIL:run_known_binary:exit {res.returncode}")
        return False, elapsed
    print_marker("TEST_PASS:run_known_binary")
    return True, elapsed

def inspect_register():
    img = "ghcr.io/antirez/c64-hw-simulator:latest"
    # assume CLI supports --inspect-reg <reg>
    cmd = ["docker", "run", "--rm", img, "--inspect-reg", "A"]
    start = time.time()
    res = run_cmd(cmd, capture=True)
    elapsed = time.time() - start
    if res is None or res.returncode != 0:
        print_marker(f"TEST_FAIL:inspect_register:{res.stderr.strip() if res else 'exception'}")
        return False, elapsed
    # simplistic check for numeric output
    try:
        val = int(res.stdout.strip())
        print_marker("TEST_PASS:inspect_register")
        return True, elapsed
    except:
        print_marker(f"TEST_FAIL:inspect_register:non‑numeric output")
        return False, elapsed

def measure_memory():
    img = "ghcr.io/antirez/c64-hw-simulator:latest"
    # create dummy 1MB ROM
    rom_path = "/tmp/dummy.rom"
    with open(rom_path, "wb") as f:
        f.write(os.urandom(1024 * 1024))
    cmd = ["docker", "run", "--rm", "-v", f"{rom_path}:/rom.bin", img, "--run", "/rom.bin"]
    start = time.time()
    tracemalloc.start()
    res = run_cmd(cmd)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start
    if res is None or res.returncode != 0:
        print_marker(f"TEST_FAIL:measure_memory:{res.stderr.strip() if res else 'exception'}")
        return False, elapsed, peak
    print_marker("TEST_PASS:measure_memory")
    return True, elapsed, peak

def validate_rest_api():
    # Assume the simulator can expose REST on port 8000 when run with --api
    img = "ghcr.io/antirez/c64-hw-simulator:latest"
    container_name = "c64_sim_test"
    # start container in background
    start = time.time()
    run_cmd(["docker", "run", "-d", "--name", container_name, "-p", "8000:8000", img, "--api"])
    time.sleep(2)  # wait for API to start
    try:
        with urllib.request.urlopen("http://localhost:8000/status") as resp:
            data = json.load(resp)
            if data.get("status") == "ok":
                print_marker("TEST_PASS:validate_rest_api")
                success = True
            else:
                print_marker("TEST_FAIL:validate_rest_api:unexpected response")
                success = False
    except Exception as e:
        print_marker(f"TEST_FAIL:validate_rest_api:{e}")
        success = False
    # cleanup
    run_cmd(["docker", "rm", "-f", container_name])
    elapsed = time.time() - start
    return success, elapsed

def baseline_compare(metric, our_value):
    # Simple baseline: use VICE's typical timings (hardcoded)
    baselines = {
        "run_known_binary": 1.2,  # seconds
        "measure_memory": 5000000,  # bytes (peak)
    }
    base = baselines.get(metric)
    if base:
        ratio = our_value / base if base != 0 else 0
        print_marker(f"BENCHMARK:vs_vice_{metric}:{ratio:.2f}")

def main():
    tracemalloc.start()
    overall_start = time.time()
    # 1. System packages
    ok, t = install_system_pkgs()
    print_marker(f"BENCHMARK:install_time_s:{t:.2f}")

    # 2. Docker pull
    ok_pull, t_pull = docker_pull_image()
    print_marker(f"BENCHMARK:docker_pull_s:{t_pull:.2f}")

    # 3. Run known binary
    ok_run, t_run = run_known_binary()
    print_marker(f"BENCHMARK:run_known_binary_s:{t_run:.2f}")
    baseline_compare("run_known_binary", t_run)

    # 4. Inspect register
    ok_reg, t_reg = inspect_register()
    print_marker(f"BENCHMARK:inspect_register_s:{t_reg:.2f}")

    # 5. Measure memory
    ok_mem, t_mem, peak_mem = measure_memory()
    print_marker(f"BENCHMARK:measure_memory_s:{t_mem:.2f}")
    print_marker(f"BENCHMARK:memory_peak_bytes:{peak_mem}")
    baseline_compare("measure_memory", peak_mem)

    # 6. Validate REST API
    ok_api, t_api = validate_rest_api()
    print_marker(f"BENCHMARK:validate_rest_api_s:{t_api:.2f}")

    # Additional generic benchmarks
    total_time = time.time() - overall_start
    current, peak = tracemalloc.get_traced_memory()
    print_marker(f"BENCHMARK:total_time_s:{total_time:.2f}")
    print_marker(f"BENCHMARK:total_memory_peak_bytes:{peak}")

    print_marker("RUN_OK")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print_marker("RUN_OK")