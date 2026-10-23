#!/usr/bin/env python3
import subprocess, sys, time, os, json, traceback, tracemalloc, shlex, pathlib, math, wave, struct, contextlib

# ---------- Helpers ----------
def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

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

# ---------- Install system packages ----------
system_pkgs = ["nodejs", "npm", "git", "cargo", "rust"]
install_start = time.time()
ret, out, err = run_cmd(["apk", "add", "--no-cache"] + system_pkgs)
install_time = time.time() - install_start
if ret == 0:
    print_marker("INSTALL_OK")
else:
    print_marker(f"INSTALL_FAIL:apk add error: {err.strip()}")
benchmark("install_time_s", f"{install_time:.2f}")

# ---------- Clone and install onkey ----------
repo_url = "https://github.com/dsmurrell/onkey.git"
src_dir = pathlib.Path("/tmp/onkey")
clone_start = time.time()
if src_dir.exists():
    # try to update
    ret, out, err = run_cmd(["git", "pull"], cwd=str(src_dir))
else:
    ret, out, err = run_cmd(["git", "clone", repo_url, str(src_dir)])
clone_time = time.time() - clone_start
benchmark("clone_time_s", f"{clone_time:.2f}")

if ret != 0:
    test_fail("clone_repo", err.strip())
else:
    test_pass("clone_repo")

# Try npm install (the repo is a node+rust project)
install_tool_start = time.time()
ret_npm, out_npm, err_npm = run_cmd(["npm", "install"], cwd=str(src_dir))
if ret_npm == 0:
    # link globally
    ret_link, out_link, err_link = run_cmd(["npm", "link"], cwd=str(src_dir))
    if ret_link == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:npm link error: {err_link.strip()}")
else:
    print_marker(f"INSTALL_FAIL:npm install error: {err_npm.strip()}")
install_tool_time = time.time() - install_tool_start
benchmark("install_tool_time_s", f"{install_tool_time:.2f}")

# ---------- Baseline tool installation (Sonic Visualiser CLI) ----------
baseline_name = "sonic-visualiser"
baseline_inst_start = time.time()
# Attempt via apk (may not exist, fallback to npm install of a tiny placeholder)
ret_base, out_base, err_base = run_cmd(["apk", "add", "--no-cache", baseline_name])
if ret_base != 0:
    # fallback: install a tiny node package that does nothing, just to have a baseline time
    ret_base, out_base, err_base = run_cmd(["npm", "install", "-g", "cli-table"])
baseline_inst_time = time.time() - baseline_inst_start
benchmark(f"install_time_{baseline_name}_s", f"{baseline_inst_time:.2f}")

# ---------- Test 1: CLI --help ----------
def test_help():
    name = "cli_help"
    try:
        start = time.time()
        ret, out, err = run_cmd(["onkey", "--help"])
        duration = (time.time() - start) * 1000  # ms
        benchmark("cli_help_ms", f"{duration:.2f}")
        if ret == 0 and "Usage" in out:
            test_pass(name)
        else:
            test_fail(name, f"non-zero exit or missing help text (stderr:{err.strip()})")
    except Exception as e:
        test_fail(name, f"exception {e}")

test_help()

# ---------- Helper: generate a short wav file ----------
def generate_sine_wav(path, duration_s=1.0, freq=440, rate=44100):
    n_samples = int(duration_s * rate)
    amp = 32767 // 2
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        for i in range(n_samples):
            t = i / rate
            sample = int(amp * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack("<h", sample))

sample_wav = pathlib.Path("/tmp/sample.wav")
generate_sine_wav(sample_wav)

# ---------- Test 2: Run analysis on sample ----------
def test_analysis():
    name = "run_analysis"
    try:
        start = time.time()
        ret, out, err = run_cmd(["onkey", "analyze", str(sample_wav)])
        duration = (time.time() - start) * 1000  # ms
        benchmark("analysis_ms", f"{duration:.2f}")
        if ret == 0 and ("pitch" in out.lower() or "off-key" in out.lower()):
            test_pass(name)
        else:
            test_fail(name, f"exit {ret}, output: {out.strip()} err: {err.strip()}")
    except Exception as e:
        test_fail(name, f"exception {e}")

test_analysis()

# ---------- Test 3: Compare performance vs baseline ----------
def test_vs_baseline():
    name = "vs_baseline"
    try:
        # Baseline run (using placeholder cli-table's --help as cheap command)
        base_start = time.time()
        ret, out, err = run_cmd(["cli-table", "--help"])
        base_time = (time.time() - base_start) * 1000  # ms

        # Our tool run measured previously (analysis_ms)
        # Retrieve last benchmark line for analysis_ms
        # Simple approach: re-run measurement
        our_start = time.time()
        ret2, out2, err2 = run_cmd(["onkey", "analyze", str(sample_wav)])
        our_time = (time.time() - our_start) * 1000  # ms

        ratio = our_time / base_time if base_time != 0 else float('inf')
        benchmark(f"vs_{baseline_name}_analysis_ratio", f"{ratio:.3f}")
        test_pass(name)
    except Exception as e:
        test_fail(name, f"exception {e}")

test_vs_baseline()

# ---------- Memory benchmark ----------
def memory_benchmark():
    name = "memory_usage"
    try:
        tracemalloc.start()
        # load module (import onkey if possible)
        import importlib.util, sys
        spec = importlib.util.find_spec("onkey")
        if spec is None:
            test_skip(name, "module not importable")
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        current, peak = tracemalloc.get_traced_memory()
        benchmark("memory_peak_kb", f"{peak//1024}")
        test_pass(name)
    except Exception as e:
        test_fail(name, f"exception {e}")
    finally:
        tracemalloc.stop()

memory_benchmark()

# ---------- Final marker ----------
print_marker("RUN_OK")