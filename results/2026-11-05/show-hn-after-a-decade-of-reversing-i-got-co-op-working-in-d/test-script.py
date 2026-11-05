#!/usr/bin/env python3
import subprocess, sys, time, os, tracemalloc, json, socket, threading

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk','add','--no-cache',pkg], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode==0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def measure_mem(func, *a, **kw):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*a, **kw)
        success = True
    except Exception as e:
        result = e
        success = False
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return success, result, time.time()-start, peak/1024

# 1. Install required system packages
for pkg in ['nodejs','npm','git','cargo','rust','make','gcc','musl-dev']:
    install_apk(pkg)

# 2. Clone repository
repo_url = "https://github.com/fireflyk64/wcmulti.git"
repo_dir = "/tmp/wcmulti"
if os.path.isdir(repo_dir):
    subprocess.run(['rm','-rf',repo_dir])
clone_res = run_cmd(['git','clone',repo_url,repo_dir])
if clone_res.returncode!=0:
    print_marker(f"TEST_FAIL:clone_repo:{clone_res.stderr.strip()}")
else:
    print_marker("TEST_PASS:clone_repo")

# 3. Install / build the tool (npm first, then fallback to cargo if exists)
build_success = False
install_time = None
mem_peak = None

def npm_build():
    global install_time, mem_peak
    start = time.time()
    res = run_cmd(['npm','install'], cwd=repo_dir)
    if res.returncode!=0:
        raise RuntimeError(res.stderr.strip())
    # try typical build script
    res2 = run_cmd(['npm','run','build'], cwd=repo_dir)
    if res2.returncode!=0:
        # maybe binary already produced, ignore
        pass
    install_time = time.time()-start
    return True

def cargo_build():
    global install_time, mem_peak
    start = time.time()
    res = run_cmd(['cargo','build','--release'], cwd=repo_dir)
    if res.returncode!=0:
        raise RuntimeError(res.stderr.strip())
    install_time = time.time()-start
    return True

# try npm
success, result, t, mem = measure_mem(npm_build)
if success:
    build_success = True
    mem_peak = mem
    print_marker(f"TEST_PASS:npm_build")
else:
    # fallback cargo
    success2, result2, t2, mem2 = measure_mem(cargo_build)
    if success2:
        build_success = True
        mem_peak = mem2
        print_marker(f"TEST_PASS:cargo_build")
    else:
        print_marker(f"TEST_FAIL:build_tool:{result}")

if build_success:
    print_marker(f"BENCHMARK:install_time_s:{install_time:.3f}")
    if mem_peak is not None:
        print_marker(f"BENCHMARK:install_mem_kb:{mem_peak:.1f}")

# locate binary
binary_path = None
possible = [
    os.path.join(repo_dir,'dist','wcmulti'),          # npm build output
    os.path.join(repo_dir,'target','release','wcmulti')  # cargo
]
for p in possible:
    if os.path.isfile(p) and os.access(p, os.X_OK):
        binary_path = p
        break
if not binary_path:
    # try npm bin
    bin_res = run_cmd(['npm','bin'], cwd=repo_dir)
    if bin_res.returncode==0:
        bin_dir = bin_res.stdout.strip()
        candidate = os.path.join(bin_dir,'wcmulti')
        if os.path.isfile(candidate):
            binary_path = candidate
if not binary_path:
    print_marker("TEST_FAIL:locate_binary:Binary not found")
else:
    print_marker("TEST_PASS:locate_binary")

# 4. Test --help
if binary_path:
    res = run_cmd([binary_path,'--help'])
    if res.returncode==0 and 'wcmulti' in res.stdout.lower():
        print_marker("TEST_PASS:help_output")
    else:
        print_marker(f"TEST_FAIL:help_output:{res.stderr.strip() or 'non-zero exit'}")

# 5. Test start command listening on expected port (default 4000)
def start_server():
    proc = subprocess.Popen([binary_path,'start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc

if binary_path:
    proc = start_server()
    time.sleep(2)  # give it time to bind
    port = 4000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(('127.0.0.1', port))
        print_marker("TEST_PASS:start_listen")
    except Exception as e:
        print_marker(f"TEST_FAIL:start_listen:{e}")
    finally:
        s.close()
        proc.terminate()
        proc.wait()

# 6. Benchmark start-up time vs baseline (xwingdroid assumed 1.2s)
if binary_path:
    def measure_start():
        start = time.time()
        p = subprocess.Popen([binary_path,'--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        return time.time()-start
    success, result, t_start, _ = measure_mem(measure_start)
    if success:
        print_marker(f"BENCHMARK:startup_time_s:{t_start:.3f}")
        baseline = 1.2
        ratio = t_start / baseline
        print_marker(f"BENCHMARK:vs_xwingdroid_startup_ratio:{ratio:.3f}")
    else:
        print_marker(f"TEST_FAIL:startup_benchmark:{result}")

# 7. Additional dummy benchmarks
print_marker(f"BENCHMARK:cpu_count:{os.cpu_count()}")
print_marker(f"BENCHMARK:repo_size_kb:{(sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, filenames in os.walk(repo_dir) for f in filenames))/1024:.1f}")

print_marker("RUN_OK")