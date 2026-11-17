import subprocess, sys, time, tracemalloc, os, shutil, json, math

# Helper to print markers
def mark(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def apk_install(pkgs):
    start = time.time()
    try:
        res = subprocess.run(['apk','add','--no-cache'] + pkgs, check=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            mark(f"INSTALL_OK")
        else:
            mark(f"INSTALL_FAIL:apk exit {res.returncode}")
    except Exception as e:
        mark(f"INSTALL_FAIL:apk exception {e}")
    finally:
        duration = time.time() - start
        mark(f"BENCHMARK:apk_install_time_s:{duration:.3f}")

def pip_install(pkg):
    start = time.time()
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', pkg],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0:
            mark("INSTALL_OK")
        else:
            mark(f"INSTALL_FAIL:pip install {pkg} exit {res.returncode}")
    except Exception as e:
        mark(f"INSTALL_FAIL:pip install {pkg} exception {e}")
    finally:
        mark(f"BENCHMARK:pip_install_{pkg}_time_s:{time.time()-start:.3f}")

def npm_install(pkg):
    start = time.time()
    try:
        res = subprocess.run(['npm','install','-g',pkg],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0:
            mark("INSTALL_OK")
        else:
            mark(f"INSTALL_FAIL:npm install {pkg} exit {res.returncode}")
    except Exception as e:
        mark(f"INSTALL_FAIL:npm install {pkg} exception {e}")
    finally:
        mark(f"BENCHMARK:npm_install_{pkg}_time_s:{time.time()-start:.3f}")

def cargo_install(pkg):
    start = time.time()
    try:
        res = subprocess.run(['cargo','install',pkg],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if res.returncode == 0:
            mark("INSTALL_OK")
        else:
            mark(f"INSTALL_FAIL:cargo install {pkg} exit {res.returncode}")
    except Exception as e:
        mark(f"INSTALL_FAIL:cargo install {pkg} exception {e}")
    finally:
        mark(f"BENCHMARK:cargo_install_{pkg}_time_s:{time.time()-start:.3f}")

# 1. Install required system packages
apk_install(['nodejs','npm','git','cargo','rust'])

# Prepare directories
BASE_DIR = "/tmp/opencode_test"
REPO_URL = "https://github.com/opencode-ai/browse"
REPO_DIR = os.path.join(BASE_DIR, "browse")
SAMPLE_REPO = os.path.join(BASE_DIR, "sample-repo")

# Clean previous runs
shutil.rmtree(BASE_DIR, ignore_errors=True)
os.makedirs(BASE_DIR, exist_ok=True)

# Helper to benchmark a function
def benchmark(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*args, **kwargs)
        success = True
        err = ""
    except Exception as e:
        result = None
        success = False
        err = str(e)
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    duration = end - start
    mark(f"BENCHMARK:{name}_time_s:{duration:.3f}")
    mark(f"BENCHMARK:{name}_memory_kb:{peak/1024:.1f}")
    return success, err, result

# 2. Clone repository
def git_clone():
    return run_cmd(['git','clone', REPO_URL, REPO_DIR])

clone_success, clone_err, _ = benchmark("git_clone", git_clone)
if clone_success and _.returncode == 0:
    mark("TEST_PASS:git_clone")
else:
    mark(f"TEST_FAIL:git_clone:{clone_err or _.stderr.strip()}")

# 3. Install the tool (try cargo first, then fallback to pip editable)
install_success = False
install_err = ""

def cargo_build():
    # assume Cargo.toml present at repo root
    return run_cmd(['cargo','install','--path', '.'], cwd=REPO_DIR)

def pip_editable():
    return run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=REPO_DIR)

# Try cargo install
cargo_ok, cargo_err, cargo_res = benchmark("cargo_install_build", cargo_build)
if cargo_ok and cargo_res.returncode == 0:
    install_success = True
    mark("TEST_PASS:cargo_install")
else:
    # fallback to pip editable
    pip_ok, pip_err, pip_res = benchmark("pip_editable_install", pip_editable)
    if pip_ok and pip_res.returncode == 0:
        install_success = True
        mark("TEST_PASS:pip_editable_install")
    else:
        install_err = pip_err or pip_res.stderr.strip()
        mark(f"TEST_FAIL:install:{install_err}")

# Helper to run CLI command and capture output
def run_cli(args, cwd=None):
    return run_cmd(['browse'] + args, cwd=cwd)

# 4. Test --help
def test_help():
    return run_cli(['--help'])

help_ok, help_err, help_res = benchmark("cli_help", test_help)
if help_ok and help_res.returncode == 0 and "Usage" in help_res.stdout:
    mark("TEST_PASS:cli_help")
else:
    mark(f"TEST_FAIL:cli_help:{help_err or help_res.stderr.strip()}")

# 5. Prepare a small sample repo for indexing
def create_sample_repo():
    os.makedirs(SAMPLE_REPO, exist_ok=True)
    # simple Rust file
    src = os.path.join(SAMPLE_REPO, "main.rs")
    with open(src, "w") as f:
        f.write('fn main() { println!("Hello world"); }\n')
    # init git
    run_cmd(['git','init'], cwd=SAMPLE_REPO)
    run_cmd(['git','add','.'], cwd=SAMPLE_REPO)
    run_cmd(['git','commit','-m','init'], cwd=SAMPLE_REPO)
    return True

sample_ok, sample_err, _ = benchmark("create_sample_repo", create_sample_repo)
if sample_ok:
    mark("TEST_PASS:create_sample_repo")
else:
    mark(f"TEST_FAIL:create_sample_repo:{sample_err}")

# 6. Index and search
def index_and_search():
    # index
    idx = run_cli(['--index', SAMPLE_REPO])
    if idx.returncode != 0:
        raise RuntimeError(f"index failed: {idx.stderr.strip()}")
    # search
    sr = run_cli(['--search', 'fn main'])
    return sr

search_ok, search_err, search_res = benchmark("index_search", index_and_search)
if search_ok and search_res.returncode == 0 and "fn main" in search_res.stdout:
    mark("TEST_PASS:index_search")
else:
    msg = search_err or search_res.stderr.strip()
    mark(f"TEST_FAIL:index_search:{msg}")

# Baseline comparison against ripgrep (rg) for simple search in same repo
def baseline_rg():
    # ensure rg is installed via apk (already part of base alpine? install if missing)
    subprocess.run(['apk','add','--no-cache','ripgrep'], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    start = time.time()
    res = run_cmd(['rg','fn','main.rs'], cwd=SAMPLE_REPO)
    duration = time.time() - start
    if res.returncode != 0:
        raise RuntimeError("rg search failed")
    return duration

baseline_ok, baseline_err, baseline_time = benchmark("baseline_rg_search", baseline_rg)
if baseline_ok:
    # compute ratio browse_time / rg_time (using previous search benchmark time)
    # retrieve browse duration from BENCHMARK lines stored earlier? We'll approximate using the last measured duration
    # Here we stored duration in variable search_res? Not directly, so re-run to get duration
    browse_duration = search_res.elapsed if hasattr(search_res, 'elapsed') else None
    # fallback: use the time measured in benchmark (last printed line). We'll capture via variable from benchmark wrapper.
    # The benchmark wrapper returns success, err, result; we didn't capture duration, so we compute again:
    def timed_browse():
        start = time.time()
        run_cli(['--search','fn main'], cwd=SAMPLE_REPO)
        return time.time() - start
    browse_time = timed_browse()
    ratio = browse_time / baseline_time if baseline_time else float('nan')
    mark(f"BENCHMARK:vs_rg_search_ratio:{ratio:.3f}")
else:
    mark(f"TEST_SKIP:baseline_rg:{baseline_err}")

# Ensure at least three benchmark lines are printed (already printed many)

# Final marker
mark("RUN_OK")