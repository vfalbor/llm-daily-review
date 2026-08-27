#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, shutil, socket, threading

# ---------- Helpers ----------
def run_cmd(cmd, cwd=None, env=None, capture=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=False,
        )
        return result
    except Exception as e:
        return e

def print_marker(line):
    print(line, flush=True)

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def test_pass(name):
    print_marker(f"TEST_PASS:{name}")

def test_fail(name, reason):
    print_marker(f"TEST_FAIL:{name}:{reason}")

def test_skip(name, reason):
    print_marker(f"TEST_SKIP:{name}:{reason}")

# ---------- 1. Install system packages ----------
apk_pkgs = ["nodejs", "npm", "git", "cargo", "rust"]
install_start = time.time()
apk_res = run_cmd(["apk", "add", "--no-cache"] + apk_pkgs)
install_time = time.time() - install_start
if isinstance(apk_res, subprocess.CompletedProcess) and apk_res.returncode == 0:
    print_marker("INSTALL_OK")
else:
    reason = getattr(apk_res, "stderr", str(apk_res))
    print_marker(f"INSTALL_FAIL:{reason}")

benchmark("install_time_s", f"{install_time:.2f}")

# ---------- 2. Clone repository ----------
repo_url = "https://github.com/tailscale/tailcat.git"
src_dir = "/tmp/tailcat_src"
if os.path.isdir(src_dir):
    shutil.rmtree(src_dir)
clone_start = time.time()
clone_res = run_cmd(["git", "clone", "--depth", "1", repo_url, src_dir])
clone_time = time.time() - clone_start
if isinstance(clone_res, subprocess.CompletedProcess) and clone_res.returncode == 0:
    test_pass("clone_repo")
else:
    test_fail("clone_repo", getattr(clone_res, "stderr", str(clone_res)))
benchmark("clone_time_s", f"{clone_time:.2f}")

# ---------- 3. Build/install tailcat ----------
build_start = time.time()
cargo_res = run_cmd(["cargo", "install", "--path", "."], cwd=src_dir)
build_time = time.time() - build_start
if isinstance(cargo_res, subprocess.CompletedProcess) and cargo_res.returncode == 0:
    test_pass("cargo_install")
else:
    test_fail("cargo_install", getattr(cargo_res, "stderr", str(cargo_res)))
benchmark("build_time_s", f"{build_time:.2f}")

# Path to installed binary (cargo places it in $HOME/.cargo/bin)
binary_path = os.path.expanduser("~/.cargo/bin/tailcat")
if not os.path.isfile(binary_path):
    test_skip("binary_exists", "binary not found after cargo install")
else:
    # ---------- 4. Test --help ----------
    help_start = time.time()
    help_res = run_cmd([binary_path, "--help"], capture=True)
    help_time = time.time() - help_start
    benchmark("help_time_s", f"{help_time:.3f}")
    if isinstance(help_res, subprocess.CompletedProcess) and help_res.returncode == 0:
        if "Usage" in help_res.stdout or "tailcat" in help_res.stdout.lower():
            test_pass("help_output")
        else:
            test_fail("help_output", "unexpected help text")
    else:
        test_fail("help_output", getattr(help_res, "stderr", str(help_res)))

    # ---------- 5. Start local echo server ----------
    echo_port = 12345
    echo_server = None
    server_thread = None
    try:
        # Use busybox nc as echo server
        server_cmd = ["nc", "-lk", str(echo_port)]
        echo_server = subprocess.Popen(server_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        # Give it a moment to start
        time.sleep(0.5)
        test_pass("start_echo_server")
    except Exception as e:
        test_fail("start_echo_server", str(e))

    # ---------- 6. Test basic connection ----------
    def run_tailcat_and_send(message):
        # Start tailcat client connecting to echo server
        client_cmd = [binary_path, f"127.0.0.1:{echo_port}"]
        client_proc = subprocess.Popen(client_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            client_proc.stdin.write(message)
            client_proc.stdin.flush()
            # Read response (echo server will send back same data)
            resp = client_proc.stdout.read(len(message))
            client_proc.terminate()
            return resp
        finally:
            client_proc.kill()

    basic_msg = "hello-tailcat"
    try:
        resp = run_tailcat_and_send(basic_msg)
        if resp == basic_msg:
            test_pass("basic_echo")
        else:
            test_fail("basic_echo", f"mismatch: got {resp!r}")
    except Exception as e:
        test_fail("basic_echo", str(e))

    # ---------- 7. Measure round‑trip latency for 1KB ----------
    payload = "A" * 1024  # 1KB
    try:
        rt_start = time.time()
        resp = run_tailcat_and_send(payload)
        rt_end = time.time()
        if resp == payload:
            latency_ms = (rt_end - rt_start) * 1000
            benchmark("rt_latency_1kb_ms", f"{latency_ms:.2f}")
            test_pass("latency_1kb")
        else:
            test_fail("latency_1kb", "payload mismatch")
    except Exception as e:
        test_fail("latency_1kb", str(e))

    # ---------- 8. Baseline comparison with netcat ----------
    # Measure same latency using plain nc as baseline
    try:
        baseline_start = time.time()
        # Use nc client to send and receive
        nc_proc = subprocess.Popen(
            ["nc", "127.0.0.1", str(echo_port)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        nc_proc.stdin.write(payload)
        nc_proc.stdin.flush()
        resp = nc_proc.stdout.read(len(payload))
        nc_proc.terminate()
        baseline_end = time.time()
        baseline_latency = (baseline_end - baseline_start) * 1000
        benchmark("baseline_nc_latency_1kb_ms", f"{baseline_latency:.2f}")
        # ratio tailcat / nc
        if 'latency_ms' in locals():
            ratio = latency_ms / baseline_latency if baseline_latency else float('inf')
            benchmark(f"vs_nc_latency_ratio", f"{ratio:.3f}")
    except Exception as e:
        test_skip("baseline_comparison", str(e))

    # Cleanup echo server
    if echo_server:
        echo_server.kill()
        echo_server.wait()

# ---------- Additional benchmarks ----------
# Memory usage snapshot
tracemalloc.start()
snapshot = tracemalloc.take_snapshot()
mem_kb = sum([stat.size for stat in snapshot.statistics('filename')]) / 1024
benchmark("memory_usage_kb", f"{mem_kb:.1f}")
tracemalloc.stop()

# Count source lines of code
loc = 0
for root, _, files in os.walk(src_dir):
    for f in files:
        if f.endswith(('.rs', '.go', '.py', '.sh')):
            try:
                with open(os.path.join(root, f), 'r', errors='ignore') as fh:
                    loc += sum(1 for _ in fh)
            except:
                pass
benchmark("loc_count", f"{loc}")

# Final marker
print_marker("RUN_OK")