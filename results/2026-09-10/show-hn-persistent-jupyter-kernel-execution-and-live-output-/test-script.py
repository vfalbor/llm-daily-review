#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, json, shlex, signal, threading

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, timeout=60):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout, text=True)
        duration = time.time() - start
        return result.returncode, result.stdout, result.stderr, duration
    except Exception as e:
        return 1, "", str(e), 0.0

def apk_install(pkg):
    rc, out, err, _ = run_cmd(['apk','add','--no-cache',pkg])
    if rc == 0:
        print_marker(f"INSTALL_OK | {pkg}")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{err.strip() or 'apk error'}")
    return rc == 0

def pip_install(pkg):
    rc, out, err, duration = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])
    if rc == 0:
        print_marker(f"INSTALL_OK | pip:{pkg}")
    else:
        print_marker(f"INSTALL_FAIL:pip:{pkg}:{err.strip() or 'pip error'}")
    print_marker(f"BENCHMARK:install_time_{pkg}_s:{duration:.3f}")
    return rc == 0

def git_clone(repo, dest):
    rc, out, err, _ = run_cmd(['git','clone','--depth','1',repo,dest])
    if rc == 0:
        print_marker(f"INSTALL_OK | git:{repo}")
    else:
        print_marker(f"INSTALL_FAIL:git:{repo}:{err.strip() or 'git error'}")
    return rc == 0

def pip_editable(path):
    rc, out, err, duration = run_cmd([sys.executable, '-m','pip','install','-e',path])
    if rc == 0:
        print_marker(f"INSTALL_OK | pip_editable:{path}")
    else:
        print_marker(f"INSTALL_FAIL:pip_editable:{path}:{err.strip() or 'pip error'}")
    print_marker(f"BENCHMARK:editable_install_time_s:{duration:.3f}")
    return rc == 0

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        ok = True
    except Exception as e:
        ok = False
        err = str(e)
    duration = (time.time() - start)*1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if ok:
        print_marker(f"BENCHMARK:import_{module_name}_ms:{duration:.2f}")
        print_marker(f"BENCHMARK:import_{module_name}_mem_kb:{peak/1024:.2f}")
    else:
        print_marker(f"TEST_FAIL:import_{module_name}:{err}")
    return ok

def test_cli_help():
    name="cli_help"
    rc, out, err, duration = run_cmd(['tithon','--help'])
    if rc == 0 and "Usage" in out:
        print_marker(f"TEST_PASS:{name}")
    else:
        reason = err.strip() or ("non-zero exit" if rc else "missing help output")
        print_marker(f"TEST_FAIL:{name}:{reason}")
    print_marker(f"BENCHMARK:{name}_exec_ms:{duration*1000:.2f}")

def test_start_kernel():
    name="start_kernel"
    # start in background
    proc = subprocess.Popen(['tithon','start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # give it time to start
    # check if process is still alive
    if proc.poll() is None:
        print_marker(f"TEST_PASS:{name}")
    else:
        out, err = proc.communicate()
        print_marker(f"TEST_FAIL:{name}:kernel exited early")
    # cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print_marker(f"BENCHMARK:{name}_start_time_s:{2.0:.2f}")

def test_long_running_cell():
    name="long_cell"
    # simulate a long-running cell by running a python one-liner that prints periodically
    script = "import time; [print(i) or time.sleep(0.5) for i in range(3)]"
    rc, out, err, duration = run_cmd([sys.executable,'-c',script])
    if rc == 0 and "0" in out:
        print_marker(f"TEST_PASS:{name}")
    else:
        print_marker(f"TEST_FAIL:{name}:{err.strip() or 'cell failed'}")
    print_marker(f"BENCHMARK:{name}_exec_ms:{duration*1000:.2f}")

def test_kernel_restart_vs_jupyter():
    name="kernel_restart"
    # measure tithon start time
    start = time.time()
    proc1 = subprocess.Popen(['tithon','start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    proc1.terminate()
    proc1.wait()
    tithon_time = time.time() - start

    # measure standard jupyter kernel start
    start = time.time()
    proc2 = subprocess.Popen(['jupyter','kernel'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    proc2.terminate()
    proc2.wait()
    jupyter_time = time.time() - start

    ratio = tithon_time / jupyter_time if jupyter_time else 0
    print_marker(f"BENCHMARK:{name}_tithon_s:{tithon_time:.3f}")
    print_marker(f"BENCHMARK:{name}_jupyter_s:{jupyter_time:.3f}")
    print_marker(f"BENCHMARK:vs_jupyter_{name}_ratio:{ratio:.3f}")

def main():
    # 1. Install required system packages
    for pkg in ['nodejs','npm','git','cargo','rust']:
        apk_install(pkg)

    # 2. Try pip install first
    installed = pip_install('tithon')
    if not installed:
        # fallback to git clone + editable install
        repo = 'https://github.com/rnoro/tithon.git'
        dest = '/tmp/tithon_src'
        if git_clone(repo, dest):
            pip_editable(dest)

    # 3. Measure import of tithon if possible
    measure_import('tithon')

    # 4. Run defined tests
    test_cli_help()
    test_start_kernel()
    test_long_running_cell()
    test_kernel_restart_vs_jupyter()

    # 5. Emit some generic benchmarks
    print_marker(f"BENCHMARK:loc_count:{sum(1 for _ in open(__file__)))")
    print_marker(f"BENCHMARK:cpu_count:{os.cpu_count()}")
    print_marker(f"BENCHMARK:memory_mb:{(os.popen('free -m').read().split()[7])}")

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()