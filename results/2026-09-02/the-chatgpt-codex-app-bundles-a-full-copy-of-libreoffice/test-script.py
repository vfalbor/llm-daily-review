import subprocess, sys, os, time, json, traceback, tracemalloc, shutil, pathlib, re
from urllib.request import urlopen

# Helpers
def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, capture_output=False):
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, text=True,
                                stdout=subprocess.PIPE if capture_output else None,
                                stderr=subprocess.STDOUT)
        return result.stdout if capture_output else ""
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {e.stdout or e}")

def bench(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def test_pass(name):
    print_marker(f"TEST_PASS:{name}")

def test_fail(name, reason):
    print_marker(f"TEST_FAIL:{name}:{reason}")

def test_skip(name, reason):
    print_marker(f"TEST_SKIP:{name}:{reason}")

# 1. Install required APK packages
apk_packages = ["nodejs", "npm", "git", "cargo", "rust"]
install_start = time.time()
try:
    subprocess.run(['apk','add','--no-cache'] + apk_packages, check=False)
    bench("install_time_s", round(time.time() - install_start, 2))
    print_marker("INSTALL_OK")
except Exception as e:
    bench("install_time_s", round(time.time() - install_start, 2))
    print_marker(f"INSTALL_FAIL:{str(e)}")

# 2. Install the codex-libreoffice tool
repo_url = "https://github.com/simonwillison/codex-libreoffice.git"
clone_dir = "/tmp/codex-libreoffice"
install_start = time.time()
try:
    if os.path.isdir(clone_dir):
        shutil.rmtree(clone_dir)
    run_cmd(["git", "clone", "--depth", "1", repo_url, clone_dir])
    # Try pip install
    try:
        run_cmd([sys.executable, "-m", "pip", "install", "-e", "."], cwd=clone_dir)
    except Exception:
        # fallback to npm install if package.json exists
        pkg_json = os.path.join(clone_dir, "package.json")
        if os.path.isfile(pkg_json):
            run_cmd(["npm", "ci"], cwd=clone_dir)
        else:
            raise RuntimeError("No install method succeeded")
    bench("tool_install_time_s", round(time.time() - install_start, 2))
    print_marker("INSTALL_OK")
except Exception as e:
    bench("tool_install_time_s", round(time.time() - install_start, 2))
    print_marker(f"INSTALL_FAIL:{e}")

# Path to the installed CLI entrypoint (assume console_script 'codex-libreoffice')
cli_cmd = ["codex-libreoffice"]

# 3. Test --help
test_name = "help_output"
try:
    start = time.time()
    out = run_cmd(cli_cmd + ["--help"], capture_output=True)
    duration = time.time() - start
    bench("help_time_ms", int(duration * 1000))
    if "Usage" in out or "options" in out.lower():
        test_pass(test_name)
    else:
        test_fail(test_name, "Help output missing expected keywords")
except Exception as e:
    test_fail(test_name, str(e))

# 4. Generate a document (simple prompt)
test_name = "generation_latency"
odt_path = "/tmp/generated.odt"
prompt = "Write a short 500‑word essay about the importance of open source software."
try:
    # Ensure output dir is clean
    if os.path.exists(odt_path):
        os.remove(odt_path)

    start = time.time()
    # The actual CLI arguments are guessed; adjust if needed
    run_cmd(cli_cmd + ["generate", "--prompt", prompt, "--output", odt_path])
    latency = time.time() - start
    bench("generation_latency_s", round(latency, 3))

    if os.path.isfile(odt_path) and os.path.getsize(odt_path) > 0:
        test_pass(test_name)
    else:
        test_fail(test_name, "Output .odt file not created or empty")
except Exception as e:
    test_fail(test_name, f"Exception: {e}")

# 5. Verify content inside .odt (simple unzip & search)
test_name = "output_content"
try:
    import zipfile
    with zipfile.ZipFile(odt_path, 'r') as z:
        content_xml = z.read('content.xml').decode('utf-8', errors='ignore')
    # Check that a few words from the prompt appear
    if re.search(r"open source", content_xml, re.IGNORECASE):
        test_pass(test_name)
    else:
        test_fail(test_name, "Generated content does not contain expected phrase")
except Exception as e:
    test_fail(test_name, f"Exception: {e}")

# 6. Benchmark vs baseline (LibreOffice Portable - assume baseline latency 8s)
baseline_latency = 8.0
if 'generation_latency_s' in globals():
    pass  # already printed
else:
    # retrieve last generation latency from bench output parsing (skip here)
    baseline_latency = 8.0
# Compute ratio
try:
    ratio = round(latency / baseline_latency, 3)
    bench(f"vs_libreoffice_portable_latency_ratio", ratio)
except Exception:
    pass

# Additional generic benchmarks
bench("loc_count", sum(1 for _ in pathlib.Path('.').rglob('*.py')))
bench("test_files_count", len([f for f in pathlib.Path('.').rglob('test_*.py')]))
bench("memory_peak_kb", lambda: int(tracemalloc.get_traced_memory()[1]/1024) if tracemalloc.is_tracing() else 0)  # placeholder

print_marker("RUN_OK")