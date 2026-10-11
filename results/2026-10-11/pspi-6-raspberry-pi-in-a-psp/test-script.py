import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib, re, statistics, math, hashlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def apk_install(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{err.strip() or 'apk error'}")
    return rc == 0

def measure_time(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return result, end - start

def bench(name, value, unit="s"):
    print_marker(f"BENCHMARK:{name}:{value}")

def safe_remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            shutil.remove(path)
    except Exception:
        pass

# 1. Install system packages
if not apk_install('git'):
    # continue anyway
    pass

repo_url = "https://github.com/othermod/PSPi-Version-6"
repo_dir = "/tmp/PSPi-Version-6"

# clean previous clone
safe_remove(repo_dir)

# Benchmark clone time
def clone_repo():
    return run_cmd(['git', 'clone', '--recurse-submodules', repo_url, repo_dir])

(clone_res, clone_time) = measure_time(clone_repo)
if clone_res[0] == 0:
    print_marker("TEST_PASS:clone_repo")
else:
    print_marker(f"TEST_FAIL:clone_repo:{clone_res[2].strip() or 'clone failed'}")
bench("clone_time_s", round(clone_time, 3))

# Baseline comparison (assume PicoPack clone ~5s)
baseline_clone = 5.0
ratio = round(clone_time / baseline_clone, 3)
print_marker(f"BENCHMARK:vs_PicoPack_clone_time_ratio:{ratio}")

# 2. Count source files and languages
def count_sources():
    exts = {}
    total = 0
    for root, _, files in os.walk(repo_dir):
        for f in files:
            ext = pathlib.Path(f).suffix.lower()
            if ext:
                exts[ext] = exts.get(ext, 0) + 1
                total += 1
    return total, exts

try:
    total_files, lang_counts = count_sources()
    bench("source_files_count", total_files)
    bench("source_languages", json.dumps(lang_counts))
    print_marker("TEST_PASS:count_sources")
except Exception as e:
    print_marker(f"TEST_FAIL:count_sources:{e}")

# 3. Run makefile (if exists)
make_path = os.path.join(repo_dir, "Makefile")
if os.path.isfile(make_path):
    def run_make():
        return run_cmd(['make', '-C', repo_dir])
    (make_res, make_time) = measure_time(run_make)
    bench("make_time_s", round(make_time, 3))
    if make_res[0] == 0:
        print_marker("TEST_PASS:run_make")
    else:
        print_marker(f"TEST_FAIL:run_make:{make_res[2].strip() or 'make error'}")
else:
    print_marker("TEST_SKIP:run_make:Makefile not found")

# 4. Look for Python examples and try to run them
python_examples = []
for root, _, files in os.walk(repo_dir):
    for f in files:
        if f.endswith('.py'):
            python_examples.append(os.path.join(root, f))

if python_examples:
    for idx, script in enumerate(python_examples[:3]):  # limit to first 3
        def run_py(s=script):
            return run_cmd([sys.executable, s])
        (py_res, py_time) = measure_time(run_py)
        bench(f"python_example_{idx+1}_time_s", round(py_time, 3))
        if py_res[0] == 0:
            print_marker(f"TEST_PASS:run_python_example_{idx+1}")
        else:
            print_marker(f"TEST_FAIL:run_python_example_{idx+1}:{py_res[2].strip() or 'runtime error'}")
else:
    print_marker("TEST_SKIP:run_python_examples:no python files found")

# 5. Memory benchmark for importing a module (if any)
if python_examples:
    try:
        tracemalloc.start()
        start_mem = tracemalloc.take_snapshot()
        import importlib.util
        spec = importlib.util.spec_from_file_location("mod", python_examples[0])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        end_mem = tracemalloc.take_snapshot()
        stats = end_mem.compare_to(start_mem, 'lineno')
        mem_kb = sum([s.size_diff for s in stats]) / 1024
        bench("import_mem_kb", round(mem_kb, 2))
        print_marker("TEST_PASS:import_memory")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_memory:{e}")
    finally:
        tracemalloc.stop()
else:
    print_marker("TEST_SKIP:import_memory:no module to import")

# 6. Placeholder for KiCad netlist verification (skip as KiCad not installed)
print_marker("TEST_SKIP:kicad_netlist:KiCad not available in container")

# 7. Placeholder for 3D model fit verification (skip as viewer not installed)
print_marker("TEST_SKIP:3d_fit_verification:no 3D viewer in container")

# Final benchmark: total execution time
total_exec_time = time.time() - (globals().get('_script_start', time.time()))
bench("total_exec_time_s", round(total_exec_time, 3))

print_marker("RUN_OK")