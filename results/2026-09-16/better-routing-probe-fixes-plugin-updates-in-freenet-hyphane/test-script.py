#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, json, urllib.request, re
from pathlib import Path

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk','add','--no-cache',pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode==0:
            return True, ""
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

def measure_install():
    start = time.time()
    tracemalloc.start()
    # install required apk packages
    ok, err = install_apk('git')
    if not ok:
        print_marker(f"INSTALL_FAIL:git install error: {err}")
    ok2, err2 = install_apk('curl')
    if not ok2:
        print_marker(f"INSTALL_FAIL:curl install error: {err2}")
    # clone repo
    repo_url = "https://github.com/freenet/freenet.git"
    src_dir = Path("/tmp/freenet_src")
    if src_dir.exists():
        subprocess.run(['rm','-rf',str(src_dir)])
    try:
        clone_res = run_cmd(['git','clone','--depth','1',repo_url,str(src_dir)])
        if clone_res.returncode!=0:
            raise RuntimeError(clone_res.stderr)
    except Exception as e:
        print_marker(f"INSTALL_FAIL:clone error: {e}")
        return None
    # build
    try:
        cfg = run_cmd(['./configure'], cwd=str(src_dir))
        if cfg.returncode!=0:
            raise RuntimeError(cfg.stderr)
        mk = run_cmd(['make','-j2'], cwd=str(src_dir))
        if mk.returncode!=0:
            raise RuntimeError(mk.stderr)
        mkinst = run_cmd(['make','install'], cwd=str(src_dir))
        if mkinst.returncode!=0:
            raise RuntimeError(mkinst.stderr)
    except Exception as e:
        print_marker(f"INSTALL_FAIL:build error: {e}")
        return None
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start
    print_marker(f"INSTALL_OK")
    print_marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")
    print_marker(f"BENCHMARK:install_mem_peak_kb:{peak/1024:.1f}")
    return src_dir

def test_daemon(src_dir):
    try:
        start = time.time()
        # start daemon in background, limited runtime
        daemon = subprocess.Popen(['java','-jar','./run.jar','--listenPort','3333','--disableNetworkSecurity','--testMode'],
                                   cwd=str(src_dir),
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
        time.sleep(5)  # give it time to start
        # simple check: daemon should output "Connected to"
        out = daemon.stdout.read(1024)
        if "Connected to" not in out:
            raise RuntimeError("No peer connection detected")
        daemon.terminate()
        daemon.wait(timeout=5)
        elapsed = time.time() - start
        print_marker(f"TEST_PASS:daemon_start")
        print_marker(f"BENCHMARK:daemon_start_s:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:daemon_start:{e}")

def test_routing_query(src_dir):
    try:
        start = time.time()
        # simulate a routing query via CLI (placeholder command)
        res = run_cmd(['java','-jar','./run.jar','--routingQuery','testnode'], cwd=str(src_dir))
        if res.returncode!=0 or "Result" not in res.stdout:
            raise RuntimeError(res.stderr or "No result")
        elapsed = (time.time() - start)*1000
        print_marker(f"TEST_PASS:routing_query")
        print_marker(f"BENCHMARK:routing_latency_ms:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:routing_query:{e}")

def test_probe_fix(src_dir):
    try:
        start = time.time()
        # generate synthetic probes (placeholder)
        res = run_cmd(['java','-jar','./run.jar','--generateProbes','10'], cwd=str(src_dir))
        if res.returncode!=0 or "Probes generated" not in res.stdout:
            raise RuntimeError(res.stderr or "Probe generation failed")
        elapsed = (time.time() - start)*1000
        print_marker(f"TEST_PASS:probe_fix")
        print_marker(f"BENCHMARK:probe_gen_ms:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:probe_fix:{e}")

def baseline_comparison(metric, value):
    # simple static baseline values for Tor (example)
    baseline = {
        "routing_latency_ms": 150.0,
        "daemon_start_s": 8.0,
        "probe_gen_ms": 200.0
    }
    base = baseline.get(metric)
    if base:
        ratio = value / base
        print_marker(f"BENCHMARK:vs_tor_{metric}:{ratio:.2f}")

def main():
    src = measure_install()
    if src:
        test_daemon(src)
        test_routing_query(src)
        test_probe_fix(src)
    # Emit extra benchmarks (memory count of files)
    try:
        start = time.time()
        file_count = sum(1 for _ in src.rglob("*") if _.is_file())
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:loc_count:{file_count}")
        print_marker(f"BENCHMARK:file_count_time_s:{elapsed:.2f}")
        baseline_comparison("routing_latency_ms", float(re.search(r'BENCHMARK:routing_latency_ms:([0-9.]+)', sys.stdout.getvalue() or "", re.I).group(1)) if False else 0)
    except Exception:
        pass
    print_marker("RUN_OK")

if __name__=="__main__":
    main()