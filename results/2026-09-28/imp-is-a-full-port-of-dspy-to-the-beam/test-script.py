import subprocess, sys, time, tracemalloc, os, json, shlex, pathlib, statistics

# Helpers for printing markers
def print_marker(msg):
    sys.stdout.flush()
    print(msg)

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
        return None

def benchmark(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        func(*args, **kwargs)
        success = True
        reason = ""
    except Exception as e:
        success = False
        reason = str(e)
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = end - start
    # Emit benchmarks
    print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.4f}")
    print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.2f}")
    return success, reason, elapsed

# 1. Install system package 'git'
apk_res = run_cmd(['apk', 'add', '--no-cache', 'git'])
if apk_res and apk_res.returncode == 0:
    print_marker("INSTALL_OK")
else:
    reason = apk_res.stderr.strip() if apk_res else "apk not found"
    print_marker(f"INSTALL_FAIL:{reason}")

# Directories
work_dir = pathlib.Path("/tmp/imp_test")
repo_url = "https://github.com/deepfates/imp.git"
repo_dir = work_dir / "imp"

# Ensure clean workspace
if work_dir.exists():
    subprocess.run(['rm', '-rf', str(work_dir)])
work_dir.mkdir(parents=True, exist_ok=True)

# 2. Clone repo
clone_res = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(repo_dir)])
if clone_res and clone_res.returncode == 0:
    print_marker("TEST_PASS:clone_repo")
else:
    print_marker(f"TEST_FAIL:clone_repo:{clone_res.stderr.strip() if clone_res else 'git clone failed'}")

# 3. Try pip install package
pip_install_ok = False
pip_err = ""
pip_res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'imp'])
if pip_res and pip_res.returncode == 0:
    pip_install_ok = True
    print_marker("TEST_PASS:pip_install")
else:
    pip_err = pip_res.stderr.strip() if pip_res else "pip not found"

# 4. Fallback: pip install -e .
if not pip_install_ok:
    fallback_res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=str(repo_dir))
    if fallback_res and fallback_res.returncode == 0:
        pip_install_ok = True
        print_marker("TEST_PASS:pip_install_editable")
    else:
        print_marker(f"TEST_FAIL:pip_install_editable:{fallback_res.stderr.strip() if fallback_res else 'fallback install failed'}")

# 5. Run mix deps.get
mix_deps_ok = False
if repo_dir.exists():
    deps_res = run_cmd(['mix', 'deps.get'], cwd=str(repo_dir))
    if deps_res and deps_res.returncode == 0:
        mix_deps_ok = True
        print_marker("TEST_PASS:mix_deps_get")
    else:
        print_marker(f"TEST_FAIL:mix_deps_get:{deps_res.stderr.strip() if deps_res else 'mix not found'}")
else:
    print_marker("TEST_SKIP:mix_deps_get:repo not cloned")

# 6. Execute example script
example_path = repo_dir / "examples" / "hello_imp.exs"
example_ok = False
if example_path.exists():
    ex_res = run_cmd(['mix', 'run', str(example_path)], cwd=str(repo_dir))
    if ex_res and ex_res.returncode == 0:
        example_ok = True
        print_marker("TEST_PASS:run_example")
    else:
        print_marker(f"TEST_FAIL:run_example:{ex_res.stderr.strip() if ex_res else 'run failed'}")
else:
    print_marker("TEST_SKIP:run_example:example not found")

# 7. Run mix test
mix_test_ok = False
test_res = run_cmd(['mix', 'test', '--no-start'], cwd=str(repo_dir))
if test_res and test_res.returncode == 0:
    mix_test_ok = True
    print_marker("TEST_PASS:mix_test")
else:
    print_marker(f"TEST_FAIL:mix_test:{test_res.stderr.strip() if test_res else 'mix test failed'}")

# 8. Benchmark prompt generation vs Python DSPy
def benchmark_imp():
    # Minimal imp usage (synthetic)
    code = """
    import imp
    from imp import Prompt
    prompt = Prompt(template="Hello {{name}}!", variables=["name"])
    _ = prompt.render(name="World")
    """
    exec(code, {})

def benchmark_dspy():
    code = """
    from dspy import Prompt
    prompt = Prompt("Hello {{name}}!", ["name"])
    _ = prompt.render(name="World")
    """
    exec(code, {})

# Ensure Python DSPy is installed for baseline
baseline_installed = False
baseline_res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'dspy-ai'])
if baseline_res and baseline_res.returncode == 0:
    baseline_installed = True

# Measure IMP
imp_success, imp_reason, imp_time = benchmark("imp_prompt", benchmark_imp)
if imp_success:
    print_marker("TEST_PASS:benchmark_imp")
else:
    print_marker(f"TEST_FAIL:benchmark_imp:{imp_reason}")

# Measure DSPy if possible
dspy_time = None
if baseline_installed:
    dspy_success, dspy_reason, dspy_time = benchmark("dspy_prompt", benchmark_dspy)
    if dspy_success:
        print_marker("TEST_PASS:benchmark_dspy")
    else:
        print_marker(f"TEST_FAIL:benchmark_dspy:{dspy_reason}")

# 9. Compare vs baseline
if dspy_time:
    ratio = imp_time / dspy_time if dspy_time > 0 else 0
    print_marker(f"BENCHMARK:vs_dspy_prompt_ratio:{ratio:.4f}")

# Ensure at least three benchmark lines (already emitted above)
# Additional simple benchmark: count python files in repo
def count_files():
    return sum(1 for _ in repo_dir.rglob("*.ex"))

file_count = count_files()
print_marker(f"BENCHMARK:repo_ex_file_count:{file_count}")

# Final marker
print_marker("RUN_OK")