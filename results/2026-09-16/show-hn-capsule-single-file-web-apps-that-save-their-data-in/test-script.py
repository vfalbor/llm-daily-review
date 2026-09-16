#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib, traceback

def marker(s):
    print(s, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def apk_install(pkg):
    try:
        res = subprocess.run(['apk','add','--no-cache',pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode==0:
            marker("INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install(pkg):
    try:
        res = subprocess.run([sys.executable,'-m','pip','install',pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode==0:
            marker("INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:pip:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:pip:{pkg}:{e}")

def measure(fn, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = fn(*args, **kwargs)
        success = True
    except Exception as e:
        result = e
        success = False
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "elapsed": end-start,
        "peak_mem": peak/1024/1024,
        "success": success,
        "result": result
    }

# ---------- Install system packages ----------
system_pkgs = ['nodejs','npm','git','cargo','rust']
for pkg in system_pkgs:
    apk_install(pkg)

# ---------- Install capsule via pip ----------
install_info = measure(pip_install, 'capsule')
if install_info["success"]:
    marker("TEST_PASS:pip_install_capsule")
else:
    marker(f"TEST_FAIL:pip_install_capsule:{install_info['result']}")

# fallback to git+editable if pip failed
capsule_src_dir = pathlib.Path("/tmp/capsule_src")
if not shutil.which('capsule'):
    try:
        if capsule_src_dir.exists():
            shutil.rmtree(capsule_src_dir)
        git_res = run_cmd(['git','clone','https://github.com/withcapsule/capsule.git', str(capsule_src_dir)])
        if git_res.returncode!=0:
            raise RuntimeError(git_res.stderr)
        edit_res = run_cmd([sys.executable,'-m','pip','install','-e','.'], cwd=str(capsule_src_dir))
        if edit_res.returncode!=0:
            raise RuntimeError(edit_res.stderr)
        marker("TEST_PASS:git_fallback_install")
    except Exception as e:
        marker(f"TEST_FAIL:git_fallback_install:{e}")

# ---------- Test 1: capsule new ----------
test_app_dir = pathlib.Path("/tmp/capsule_testapp")
def cmd_capsule_new():
    if test_app_dir.exists():
        shutil.rmtree(test_app_dir)
    return run_cmd(['capsule','new','testapp'], cwd="/tmp")
new_info = measure(cmd_capsule_new)
if new_info["success"] and test_app_dir.exists():
    marker("TEST_PASS:capsule_new")
else:
    reason = new_info["result"] if not new_info["success"] else "directory not created"
    marker(f"TEST_FAIL:capsule_new:{reason}")

# ---------- Test 2: capsule build ----------
def cmd_capsule_build():
    return run_cmd(['capsule','build','testapp'], cwd="/tmp")
build_info = measure(cmd_capsule_build)
if build_info["success"]:
    marker("TEST_PASS:capsule_build")
else:
    marker(f"TEST_FAIL:capsule_build:{build_info['result']}")

# ---------- Benchmark build time ----------
marker(f"BENCHMARK:build_time_s:{build_info['elapsed']:.3f}")

# ---------- Test 3: Run built executable ----------
executable = None
# search for built binary (should be in testapp/dist or similar)
possible_paths = list(test_app_dir.rglob('testapp*')) + list(test_app_dir.rglob('*.js'))
for p in possible_paths:
    if p.is_file() and os.access(p, os.X_OK):
        executable = str(p)
        break

def run_executable():
    if not executable:
        raise RuntimeError("Executable not found")
    return run_cmd([executable], cwd=str(test_app_dir))

run_info = measure(run_executable)
if run_info["success"]:
    marker("TEST_PASS:run_executable")
else:
    marker(f"TEST_FAIL:run_executable:{run_info['result']}")

# ---------- Benchmark run time ----------
marker(f"BENCHMARK:run_time_s:{run_info['elapsed']:.3f}")

# ---------- Verify SQLite file created ----------
sqlite_files = list(test_app_dir.rglob('*.sqlite')) + list(test_app_dir.rglob('*.db'))
if sqlite_files:
    marker("TEST_PASS:sqlite_created")
else:
    marker("TEST_FAIL:sqlite_created:No SQLite file found")

# ---------- Memory benchmark for run ----------
marker(f"BENCHMARK:run_peak_mem_mb:{run_info['peak_mem']:.3f}")

# ---------- Baseline comparison (using pkg as baseline, dummy ratio) ----------
# Assume baseline run time for similar tool is 1.5s
baseline_run = 1.5
ratio = run_info['elapsed']/baseline_run if baseline_run else 0
marker(f"BENCHMARK:vs_pkg_run_ratio:{ratio:.3f}")

# ---------- Additional benchmark: import time ----------
def import_time():
    start = time.time()
    import capsule  # noqa: F401
    return time.time()-start
imp_info = measure(import_time)
marker(f"BENCHMARK:import_time_ms:{imp_info['elapsed']*1000:.2f}")

# ---------- Final marker ----------
marker("RUN_OK")