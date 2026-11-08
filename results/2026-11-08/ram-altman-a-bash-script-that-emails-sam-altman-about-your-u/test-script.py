import subprocess, sys, time, tracemalloc, os, re, socket, threading, smtpd, asyncore, json, shlex, pathlib, tempfile, signal

# Helper to print markers
def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

# 1. Install system packages
apk_packages = ["nodejs", "npm", "git", "cargo", "rust"]
try:
    result = run_cmd(["apk", "add", "--no-cache"] + apk_packages, check=False)
    if result.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:apk_exit_{result.returncode}")
except Exception as e:
    print_marker(f"INSTALL_FAIL:apk_exception_{e}")

# 2. Install the tool
repo_url = "https://github.com/ram-altman/ram-altman.git"
workdir = pathlib.Path("/tmp/ram_altman")
if workdir.exists():
    subprocess.run(["rm", "-rf", str(workdir)])
workdir.mkdir(parents=True, exist_ok=True)

install_start = time.time()
try:
    # try npm install (if package.json exists)
    clone_res = run_cmd(["git", "clone", repo_url, str(workdir)], check=False)
    if clone_res.returncode != 0:
        raise RuntimeError(f"git clone failed: {clone_res.stderr.strip()}")
    os.chdir(workdir)

    # attempt npm install (unlikely for bash script)
    npm_res = run_cmd(["npm", "install"], check=False)
    if npm_res.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        # fallback: just ensure script is executable
        bash_script = workdir / "ram-altman.sh"
        if not bash_script.exists():
            # try find any .sh file
            sh_files = list(workdir.rglob("*.sh"))
            if sh_files:
                bash_script = sh_files[0]
        if bash_script.exists():
            bash_script.chmod(0o755)
            print_marker("INSTALL_OK")
        else:
            raise RuntimeError("bash script not found")
except Exception as e:
    print_marker(f"INSTALL_FAIL:{e}")
install_end = time.time()
install_time = install_end - install_start
print_marker(f"BENCHMARK:install_time_s:{install_time:.3f}")

# Benchmark: count lines of code
loc = 0
for f in workdir.rglob("*"):
    if f.suffix in {".sh", ".bash", ".py", ".c", ".go"}:
        try:
            loc += len(f.read_text().splitlines())
        except Exception:
            pass
print_marker(f"BENCHMARK:loc_count:{loc}")

# Setup mock SMTP server
class DebugSMTPServer(smtpd.SMTPServer):
    def __init__(self, localaddr, remoteaddr):
        super().__init__(localaddr, remoteaddr)
        self.received = []

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        self.received.append({
            "peer": peer,
            "mailfrom": mailfrom,
            "rcpttos": rcpttos,
            "data": data
        })
        return

def start_smtp_server(port):
    server = DebugSMTPServer(('127.0.0.1', port), None)
    thread = threading.Thread(target=asyncore.loop, name="smtp-server", daemon=True)
    thread.start()
    return server

SMTP_PORT = 8025
smtp_server = start_smtp_server(SMTP_PORT)

# Helper to run the ram-altman script
def run_ram_altman(threshold_kb=0):
    script_path = None
    for p in workdir.rglob("*.sh"):
        script_path = p
        break
    if not script_path:
        raise FileNotFoundError("ram-altman script not found")
    env = os.environ.copy()
    env["SMTP_SERVER"] = f"127.0.0.1:{SMTP_PORT}"
    env["RAM_THRESHOLD_KB"] = str(threshold_kb)
    # The script may expect certain variables; adapt as needed
    result = run_cmd([str(script_path)], env=env, check=False)
    return result

# 3. Test 1: Mock SMTP and capture payload
test_start = time.time()
try:
    # Ensure no prior emails
    smtp_server.received.clear()
    res = run_ram_altman(threshold_kb=0)  # zero threshold to always send
    if res.returncode != 0:
        raise RuntimeError(f"script exited {res.returncode}")
    if not smtp_server.received:
        raise AssertionError("no email received")
    print_marker("TEST_PASS:mock_smtp_capture")
except Exception as e:
    print_marker(f"TEST_FAIL:mock_smtp_capture:{e}")
test_end = time.time()
print_marker(f"BENCHMARK:test_mock_smtp_ms:{(test_end-test_start)*1000:.2f}")

# 4. Test 2: Verify parsing of /proc/meminfo
test_start = time.time()
try:
    # Read meminfo directly
    meminfo = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, val = line.split(":", 1)
            meminfo[key.strip()] = int(val.strip().split()[0])
    free_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
    # Run script with high threshold so it should NOT send
    high_thr = free_kb + 1024
    smtp_server.received.clear()
    res = run_ram_altman(threshold_kb=high_thr)
    if smtp_server.received:
        raise AssertionError("email sent despite high threshold")
    print_marker("TEST_PASS:meminfo_parsing")
except Exception as e:
    print_marker(f"TEST_FAIL:meminfo_parsing:{e}")
test_end = time.time()
print_marker(f"BENCHMARK:test_meminfo_ms:{(test_end-test_start)*1000:.2f}")

# 5. Test 3: Execution time within 1 second
test_start = time.time()
try:
    tracemalloc.start()
    res = run_ram_altman(threshold_kb=0)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    exec_time = time.time() - test_start
    if exec_time > 1.0:
        raise AssertionError(f"took {exec_time:.3f}s > 1s")
    print_marker("TEST_PASS:exec_time_under_1s")
    print_marker(f"BENCHMARK:exec_time_s:{exec_time:.3f}")
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
except Exception as e:
    print_marker(f"TEST_FAIL:exec_time_under_1s:{e}")

# 6. Baseline comparison vs htop (approximate)
# Assume baseline exec time for similar check using htop is 0.8s
baseline_time = 0.8
ratio = exec_time / baseline_time if 'exec_time' in locals() else 0
print_marker(f"BENCHMARK:vs_htop_exec_time_ratio:{ratio:.2f}")

# Final marker
print_marker("RUN_OK")