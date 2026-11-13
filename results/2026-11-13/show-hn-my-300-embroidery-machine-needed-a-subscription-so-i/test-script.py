#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, shutil, json, re

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, capture=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=True,
        )
        return result.stdout if capture else ""
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {e.stderr.strip() or e}")

def measure(fn, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = fn(*args, **kwargs)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    elapsed = time.time() - start
    return result, elapsed, peak / 1024  # KiB

# 1. Install system packages
try:
    run_cmd(['apk', 'add', '--no-cache', 'git'])
    print_marker("INSTALL_OK")
except Exception as e:
    print_marker(f"INSTALL_FAIL:{e}")

repo_url = "https://github.com/simpsoka/zigzag"
repo_dir = "/tmp/zigzag"

# Benchmarks storage
benchmarks = {}

# 2. Clone repository
def clone_repo():
    if os.path.isdir(repo_dir):
        shutil.rmtree(repo_dir)
    run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])

try:
    _, t_clone, mem_clone = measure(clone_repo)
    benchmarks['clone_time_s'] = t_clone
    print_marker(f"BENCHMARK:clone_time_s:{t_clone:.3f}")
except Exception as e:
    print_marker(f"TEST_FAIL:clone_repo:{e}")

# 3. Count source files and languages
def count_sources():
    langs = {}
    total = 0
    for root, _, files in os.walk(repo_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                langs[ext] = langs.get(ext, 0) + 1
                total += 1
    return total, langs

try:
    (src_count, lang_counts), t_count, _ = measure(count_sources)
    benchmarks['src_count'] = src_count
    print_marker(f"BENCHMARK:src_count:{src_count}")
    # also emit language breakdown as a single line (optional)
    print_marker(f"BENCHMARK:languages:{json.dumps(lang_counts)}")
    print_marker(f"TEST_PASS:source_count")
except Exception as e:
    print_marker(f"TEST_FAIL:source_count:{e}")

# 4. Build ZigZag executable (assume Rust or Zig, fallback to make)
def build_executable():
    # Try cargo if Cargo.toml exists
    if os.path.isfile(os.path.join(repo_dir, "Cargo.toml")):
        run_cmd(['apk', 'add', '--no-cache', 'rust', 'cargo'])
        run_cmd(['cargo', 'build', '--release'], cwd=repo_dir)
        return os.path.join(repo_dir, "target", "release", "zigzag")
    # Try make
    if os.path.isfile(os.path.join(repo_dir, "Makefile")):
        run_cmd(['apk', 'add', '--no-cache', 'make', 'gcc'])
        run_cmd(['make'], cwd=repo_dir)
        # guess binary name
        for candidate in ["zigzag", "zigzag.exe"]:
            path = os.path.join(repo_dir, candidate)
            if os.path.isfile(path):
                return path
    raise RuntimeError("No known build method found")

binary_path = None
try:
    binary_path, t_build, _ = measure(build_executable)
    benchmarks['build_time_s'] = t_build
    print_marker(f"BENCHMARK:build_time_s:{t_build:.3f}")
    print_marker("TEST_PASS:build")
except Exception as e:
    print_marker(f"TEST_FAIL:build:{e}")

# 5. Run CLI '--help'
def run_help():
    if not binary_path:
        raise RuntimeError("Binary not built")
    out = run_cmd([binary_path, '--help'], capture=True)
    if not out.lower().startswith('usage'):
        raise RuntimeError("Help output does not contain usage")
    return out

try:
    help_out, t_help, _ = measure(run_help)
    benchmarks['help_time_ms'] = t_help * 1000
    print_marker(f"BENCHMARK:help_time_ms:{benchmarks['help_time_ms']:.1f}")
    print_marker("TEST_PASS:cli_help")
except Exception as e:
    print_marker(f"TEST_FAIL:cli_help:{e}")

# 6. Simulated machine test (mocked via simple TCP server)
import threading, socket

SIM_HOST = "127.0.0.1"
SIM_PORT = 56789
received_commands = []

def simulator():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((SIM_HOST, SIM_PORT))
    srv.listen(1)
    conn, _ = srv.accept()
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            received_commands.append(data.decode())
    srv.close()

sim_thread = threading.Thread(target=simulator, daemon=True)
sim_thread.start()
time.sleep(0.2)  # give it time to start

def run_pattern():
    if not binary_path:
        raise RuntimeError("Binary not built")
    # Assume the CLI accepts --host and --port for remote machine
    cmd = [binary_path, 'run', '--host', SIM_HOST, '--port', str(SIM_PORT), '--pattern', 'test']
    run_cmd(cmd)

try:
    _, t_pattern, _ = measure(run_pattern)
    benchmarks['pattern_time_ms'] = t_pattern * 1000
    print_marker(f"BENCHMARK:pattern_time_ms:{benchmarks['pattern_time_ms']:.1f}")
    # simple verification
    if not received_commands:
        raise RuntimeError("No command received by simulator")
    print_marker("TEST_PASS:pattern_execution")
except Exception as e:
    print_marker(f"TEST_FAIL:pattern_execution:{e}")

# 7. Emit additional benchmarks (memory usage, file count)
benchmarks['file_count'] = src_count
print_marker(f"BENCHMARK:file_count:{src_count}")

# 8. Compare against baseline (EmbroideryScript) - dummy baseline numbers
baseline = {
    "build_time_s": 12.0,
    "help_time_ms": 50.0,
    "pattern_time_ms": 200.0,
}
for metric, value in benchmarks.items():
    if metric in baseline:
        ratio = value / baseline[metric] if baseline[metric] else 0
        print_marker(f"BENCHMARK:vs_embroideryscript_{metric}:{ratio:.3f}")

# Final marker
print_marker("RUN_OK")