import subprocess, sys, time, os, json, tracemalloc, shlex, pathlib, shutil, textwrap

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    start = time.time()
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, check=False)
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, time.time() - start

def install_apk(pkgs):
    try:
        subprocess.run(['apk', 'add', '--no-cache'] + pkgs, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        marker("INSTALL_OK")
    except Exception as e:
        marker(f"INSTALL_FAIL:{e}")

def install_npm_package(pkg):
    try:
        result, _ = run_cmd(['npm', 'install', '-g', pkg])
        if result and result.returncode == 0:
            marker("INSTALL_OK")
        else:
            reason = (result.stderr if result else "unknown error")
            marker(f"INSTALL_FAIL:{reason.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{e}")

def benchmark(name, value):
    marker(f"BENCHMARK:{name}:{value}")

def safe_test(name, func):
    try:
        func()
        marker(f"TEST_PASS:{name}")
    except Exception as e:
        marker(f"TEST_FAIL:{name}:{e}")

# 1. Install required system packages
install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])

# 2. Install ladybird via npm
def test_install_ladybird():
    install_npm_package('ladybird')
safe_test("install_ladybird", test_install_ladybird)

# Prepare a temporary directory for scaffolding
workdir = pathlib.Path("/tmp/ladybird_test")
if workdir.exists():
    shutil.rmtree(workdir)
workdir.mkdir(parents=True)

# 3. Scaffold a sample project and benchmark
def test_scaffold():
    start = time.time()
    result, _ = run_cmd(['ladybird', 'init', '--name', 'sample-app', '--template', 'basic'], cwd=workdir)
    elapsed = time.time() - start
    benchmark("scaffold_time_s", round(elapsed, 3))
    if result.returncode != 0:
        raise RuntimeError(f"ladybird init failed: {result.stderr.strip()}")
safe_test("scaffold_project", test_scaffold)

project_dir = workdir / "sample-app"

# 4. Install project dependencies (npm install) and benchmark
def test_npm_install():
    if not project_dir.is_dir():
        raise RuntimeError("Project directory not found")
    start = time.time()
    result, _ = run_cmd(['npm', 'install'], cwd=project_dir)
    elapsed = time.time() - start
    benchmark("npm_install_time_s", round(elapsed, 3))
    if result.returncode != 0:
        raise RuntimeError(f"npm install failed: {result.stderr.strip()}")
safe_test("npm_install", test_npm_install)

# 5. Build the project and benchmark
def test_build():
    start = time.time()
    result, _ = run_cmd(['npm', 'run', 'build'], cwd=project_dir)
    elapsed = time.time() - start
    benchmark("build_time_s", round(elapsed, 3))
    if result.returncode != 0:
        raise RuntimeError(f"npm run build failed: {result.stderr.strip()}")
safe_test("build_project", test_build)

# 6. Run ladybird test command (if exists) and benchmark
def test_ladybird_test():
    start = time.time()
    result, _ = run_cmd(['ladybird', 'test'], cwd=project_dir)
    elapsed = time.time() - start
    benchmark("ladybird_test_time_s", round(elapsed, 3))
    if result.returncode != 0:
        raise RuntimeError(f"ladybird test failed: {result.stderr.strip()}")
safe_test("ladybird_test", test_ladybird_test)

# Baseline comparison with Vite (assume vite is installed globally)
def compare_with_vite():
    # Scaffold with vite for baseline
    vite_dir = workdir / "vite-sample"
    if vite_dir.exists():
        shutil.rmtree(vite_dir)
    start = time.time()
    result, _ = run_cmd(['npm', 'create', 'vite@latest', 'vite-sample', '--', '--template', 'vanilla'], cwd=workdir)
    scaffold_time = time.time() - start
    benchmark("vite_scaffold_time_s", round(scaffold_time, 3))
    # Install and build vite project
    start = time.time()
    result, _ = run_cmd(['npm', 'install'], cwd=vite_dir)
    install_time = time.time() - start
    benchmark("vite_npm_install_time_s", round(install_time, 3))
    start = time.time()
    result, _ = run_cmd(['npm', 'run', 'build'], cwd=vite_dir)
    build_time = time.time() - start
    benchmark("vite_build_time_s", round(build_time, 3))
    # Ratio comparisons
    try:
        # use previously measured scaffold_time for ladybird
        lb_scaffold = float([line for line in sys.stdout.getvalue().splitlines() if line.startswith("BENCHMARK:scaffold_time_s")][0].split(":")[2])
        ratio = round(scaffold_time / lb_scaffold, 3) if lb_scaffold else 0
        benchmark(f"vs_vite_scaffold_ratio", ratio)
    except Exception:
        pass
safe_test("compare_vite", compare_with_vite)

# Final marker
marker("RUN_OK")