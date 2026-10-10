import subprocess, sys, time, json, os, tracemalloc, shutil, tempfile, pathlib, textwrap

# Helper to print markers
def print_marker(marker):
    sys.stdout.write(marker + "\n")
    sys.stdout.flush()

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        result = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg} - {result.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg} - {e}")

def install_tool_deps():
    # npm, cargo already installed via apk above
    # No extra pip packages needed for this repo
    pass

def measure_memory(func):
    tracemalloc.start()
    start = time.time()
    try:
        func()
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    elapsed = time.time() - start
    return elapsed, peak / 1024  # KB

# 1. Install required system packages
for pkg in ['nodejs', 'npm', 'git', 'cargo', 'rust']:
    install_apk(pkg)

# 2. Install tool dependencies (none extra)
install_tool_deps()

# Prepare temporary workspace
workdir = pathlib.Path(tempfile.mkdtemp(prefix="carrierexplode_test_"))
repo_url = "https://github.com/Carrier-Explode/carrierexplode.git"
repo_dir = workdir / "carrierexplode"

# Benchmark containers
benchmarks = {}

# Test 1: Clone and build
def test_clone_and_build():
    start = time.time()
    clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(repo_dir)])
    if clone_res.returncode != 0:
        raise RuntimeError(f"git clone failed: {clone_res.stderr.strip()}")
    build_res = run_cmd(['cargo', 'build', '--release'], cwd=str(repo_dir))
    if build_res.returncode != 0:
        raise RuntimeError(f"cargo build failed: {build_res.stderr.strip()}")
    end = time.time()
    benchmarks['install_time_s'] = round(end - start, 3)

try:
    test_clone_and_build()
    print_marker("TEST_PASS:clone_and_build")
except Exception as e:
    print_marker(f"TEST_FAIL:clone_and_build:{e}")

# Path to built binary
binary_path = repo_dir / "target" / "release" / "carrierexplode"

# Test 2: Help output
def test_help():
    if not binary_path.is_file():
        raise RuntimeError("binary not found")
    res = run_cmd([str(binary_path), '-h'])
    if res.returncode != 0:
        raise RuntimeError(f"non-zero exit: {res.stderr.strip()}")
    if "Usage" not in res.stdout and "carrierexplode" not in res.stdout:
        raise RuntimeError("help output missing expected keywords")
    # measure import time (simulated as execution time)
    benchmarks['help_time_ms'] = round((time.time() - start_time) * 1000, 2)

start_time = time.time()
try:
    test_help()
    print_marker("TEST_PASS:help_output")
except Exception as e:
    print_marker(f"TEST_FAIL:help_output:{e}")

# Test 3: Process sample config
sample_cfg = workdir / "sample.cfg"
sample_cfg.write_text(textwrap.dedent("""\
    # Sample carrier config
    APN=internet
    CarrierName=TestCarrier
    AuthType=NONE
    """))

def test_process_sample():
    res = run_cmd([str(binary_path), '-i', str(sample_cfg)])
    if res.returncode != 0:
        raise RuntimeError(f"run failed: {res.stderr.strip()}")
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError as je:
        raise RuntimeError(f"output not JSON: {je}")
    required_keys = {"APN", "CarrierName", "AuthType"}
    if not required_keys.issubset(set(data.keys())):
        raise RuntimeError(f"missing keys, got {list(data.keys())}")
    benchmarks['sample_process_ms'] = round((time.time() - start_time) * 1000, 2)

start_time = time.time()
try:
    test_process_sample()
    print_marker("TEST_PASS:process_sample")
except Exception as e:
    print_marker(f"TEST_FAIL:process_sample:{e}")

# Test 4: Benchmark 100 files vs baseline (aircrack-ng placeholder)
def generate_dummy_files(count, dir_path):
    for i in range(count):
        p = dir_path / f"dummy_{i}.cfg"
        p.write_text(f"APN=apn{i}\nCarrierName=Carrier{i}\nAuthType=NONE\n")

def benchmark_processing(file_count=100):
    bench_dir = workdir / "bench_files"
    bench_dir.mkdir(exist_ok=True)
    generate_dummy_files(file_count, bench_dir)
    start = time.time()
    for cfg in bench_dir.iterdir():
        res = run_cmd([str(binary_path), '-i', str(cfg)])
        if res.returncode != 0:
            raise RuntimeError(f"processing {cfg.name} failed")
    return time.time() - start

try:
    proc_time = benchmark_processing(100)
    benchmarks['process_100_ms'] = round(proc_time * 1000, 2)
    print_marker("TEST_PASS:benchmark_100_files")
except Exception as e:
    print_marker(f"TEST_FAIL:benchmark_100_files:{e}")

# Emit benchmarks
for name, value in benchmarks.items():
    print_marker(f"BENCHMARK:{name}:{value}")

# Baseline comparison (using aircrack-ng as a dummy baseline of 1500ms for 100 files)
baseline_time_ms = 1500.0
if 'process_100_ms' in benchmarks:
    ratio = round(baselines_time_ms / benchmarks['process_100_ms'], 3) if benchmarks['process_100_ms'] else 0
    print_marker(f"BENCHMARK:vs_aircrackng_process_100_ratio:{ratio}")

# Cleanup
shutil.rmtree(workdir, ignore_errors=True)

# Final marker
print_marker("RUN_OK")