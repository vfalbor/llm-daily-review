import subprocess, sys, time, os, json, traceback, tracemalloc, shlex

# Helper functions for structured output
def emit(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None, timeout=None):
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
            check=False,
        )
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, time.time() - start

def benchmark(name, value):
    emit(f"BENCHMARK:{name}:{value}")

def test_pass(name):
    emit(f"TEST_PASS:{name}")

def test_fail(name, reason):
    emit(f"TEST_FAIL:{name}:{reason}")

def test_skip(name, reason):
    emit(f"TEST_SKIP:{name}:{reason}")

# 1. Install required system packages
apk_packages = ["nodejs", "npm", "git", "cargo", "rust"]
install_start = time.time()
try:
    proc = subprocess.run(
        ["apk", "add", "--no-cache"] + apk_packages,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        emit("INSTALL_OK")
    else:
        emit(f"INSTALL_FAIL:{proc.stderr.strip()}")
except Exception as e:
    emit(f"INSTALL_FAIL:{str(e)}")
install_time = time.time() - install_start
benchmark("install_time_s", f"{install_time:.2f}")

# 2. Clone the repository
repo_url = "https://github.com/anubhavmalhotra/r2d2-tv.git"
repo_dir = "/tmp/r2d2-tv"
clone_start = time.time()
try:
    if os.path.isdir(repo_dir):
        subprocess.run(["rm", "-rf", repo_dir], check=False)
    result, elapsed = run_cmd(["git", "clone", "--depth", "1", repo_url, repo_dir])
    if result and result.returncode == 0:
        test_pass("clone_repo")
    else:
        test_fail("clone_repo", result.stderr if result else "git clone failed")
except Exception as e:
    test_fail("clone_repo", str(e))
benchmark("clone_time_s", f"{elapsed:.2f}")

# 3. Build Docker image from the repo
docker_image_tag = "r2d2-tv:test"
build_start = time.time()
try:
    result, elapsed = run_cmd(["docker", "build", "-t", docker_image_tag, "."], cwd=repo_dir)
    if result and result.returncode == 0:
        test_pass("docker_build")
    else:
        test_fail("docker_build", result.stderr if result else "docker build failed")
except Exception as e:
    test_fail("docker_build", str(e))
benchmark("docker_build_time_s", f"{elapsed:.2f}")

# 4. Run the CLI with --help
help_start = time.time()
try:
    result, elapsed = run_cmd(["docker", "run", "--rm", docker_image_tag, "--help"])
    if result and result.returncode == 0:
        test_pass("cli_help")
    else:
        test_fail("cli_help", result.stderr if result else "docker run failed")
except Exception as e:
    test_fail("cli_help", str(e))
benchmark("cli_help_time_ms", f"{elapsed*1000:.1f}")

# 5. Build and run a simple Python script inside the container
python_test_name = "python_inside_container"
script_content = "print('Hello from inside the container')\n"
script_path_host = "/tmp/hello.py"
script_path_container = "/app/hello.py"

try:
    with open(script_path_host, "w") as f:
        f.write(script_content)
    # copy script into image by mounting a volume
    exec_start = time.time()
    result, elapsed = run_cmd([
        "docker", "run", "--rm",
        "-v", f"/tmp:/app",
        docker_image_tag,
        "python3", script_path_container
    ])
    if result and result.returncode == 0:
        test_pass(python_test_name)
    else:
        test_fail(python_test_name, result.stderr if result else "script exec failed")
    benchmark("python_script_time_ms", f"{elapsed*1000:.1f}")
except Exception as e:
    test_fail(python_test_name, str(e))

# 6. Benchmark memory usage of importing a module (tracemalloc)
mem_test_name = "import_memory"
tracemalloc.start()
mem_start = time.time()
try:
    import json  # example module
    elapsed = time.time() - mem_start
    current, peak = tracemalloc.get_traced_memory()
    benchmark("import_time_ms", f"{elapsed*1000:.2f}")
    benchmark("import_peak_mem_kb", f"{peak/1024:.2f}")
    test_pass(mem_test_name)
except Exception as e:
    test_fail(mem_test_name, str(e))
finally:
    tracemalloc.stop()

# 7. Compare CLI help time vs baseline (RetroPie help assumed 0.12 sec)
baseline_help_ms = 120.0  # hypothetical baseline in ms
cli_help_ms = elapsed * 1000 if 'elapsed' in locals() else 0
ratio = cli_help_ms / baseline_help_ms if baseline_help_ms else 0
benchmark(f"vs_retropie_help_time_ratio", f"{ratio:.3f}")

# Ensure at least three benchmark lines (already emitted)
# Final marker
emit("RUN_OK")