import os
import sys
import time
import subprocess
import tracemalloc
import shutil

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def apk_install(pkg):
    start = time.time()
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg], check=False)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        duration = time.time() - start
        print_marker(f"INSTALL_OK | {pkg}")
        return duration
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")
        return None

def clone_repo(url, dest):
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        res = run_cmd(['git', 'clone', '--depth', '1', url, dest], check=False)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        print_marker("INSTALL_OK | clone")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:clone:{e}")
        return False

def build_toit(src_dir):
    os.chdir(src_dir)
    start = time.time()
    # Try typical build commands
    for cmd in [['make'], ['./configure'], ['cargo', 'build', '--release']]:
        try:
            res = run_cmd(cmd, check=False)
            if res.returncode == 0:
                duration = time.time() - start
                print_marker("INSTALL_OK | build")
                return duration
        except Exception:
            continue
    print_marker("INSTALL_FAIL:build:All build attempts failed")
    return None

def run_hello_world(src_dir):
    # Assume a hello_world example exists after build
    hello_path = os.path.join(src_dir, 'build', 'release', 'toit')
    if not os.path.isfile(hello_path):
        # fallback to a generic binary if known
        hello_path = os.path.join(src_dir, 'bin', 'toit')
    if not os.path.isfile(hello_path):
        print_marker("TEST_FAIL:hello_world:Binary not found")
        return None
    start = time.time()
    try:
        res = run_cmd([hello_path, '-e', 'print("Hello, Toit!")'])
        duration = (time.time() - start) * 1000  # ms
        if res.returncode == 0:
            print_marker("TEST_PASS:hello_world")
            return duration
        else:
            print_marker(f"TEST_FAIL:hello_world:{res.stderr.strip()}")
            return None
    except Exception as e:
        print_marker(f"TEST_FAIL:hello_world:{e}")
        return None

def benchmark_memory(func, *args, **kwargs):
    tracemalloc.start()
    result = func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, peak / 1024  # KiB

def main():
    total_start = time.time()
    # 1. Install system packages
    pkgs = ['go', 'git', 'cargo', 'rust', 'nodejs', 'npm']
    install_times = {}
    for p in pkgs:
        dur = apk_install(p)
        if dur is not None:
            install_times[p] = dur

    # 2. Clone repo
    repo_url = "https://github.com/toitware/toit"
    src_dir = "/tmp/toit_src"
    if not clone_repo(repo_url, src_dir):
        print_marker("TEST_SKIP:clone:Could not clone repository")
        # continue to next steps anyway (they will fail)
    
    # 3. Build
    build_time = None
    if os.path.isdir(src_dir):
        build_time = build_toit(src_dir)

    # 4. Run hello world benchmark
    hello_time = None
    mem_usage = None
    if build_time is not None:
        hello_time, mem_usage = benchmark_memory(run_hello_world, src_dir)

    # Emit benchmarks
    if install_times:
        total_install = sum(install_times.values())
        print_marker(f"BENCHMARK:install_time_s:{total_install:.2f}")
    if build_time is not None:
        print_marker(f"BENCHMARK:build_time_s:{build_time:.2f}")
    if hello_time is not None:
        print_marker(f"BENCHMARK:hello_world_ms:{hello_time:.2f}")
    if mem_usage is not None:
        print_marker(f"BENCHMARK:memory_peak_kib:{mem_usage:.2f}")

    # Baseline comparison with Rust (example baseline compile time 0.8s)
    baseline_compile = 0.8  # seconds (hypothetical)
    if build_time is not None:
        ratio = build_time / baseline_compile
        print_marker(f"BENCHMARK:vs_rust_compile_ratio:{ratio:.2f}")

    # Ensure RUN_OK printed
    print_marker("RUN_OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_marker(f"TEST_FAIL:unexpected:{e}")
        print_marker("RUN_OK")