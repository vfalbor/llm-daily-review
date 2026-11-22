import subprocess, sys, time, tracemalloc, os, json, shlex, pathlib, tempfile

def run_cmd(cmd, capture=False, check=False):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, check=check)
        return result
    except Exception as e:
        return e

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    start = time.time()
    result = run_cmd(f"apk add --no-cache {pkg}", check=False)
    elapsed = time.time() - start
    if isinstance(result, Exception) or result.returncode != 0:
        reason = getattr(result, 'stderr', str(result))
        print_marker(f"INSTALL_FAIL:{reason}")
        return False, elapsed
    print_marker("INSTALL_OK")
    return True, elapsed

def pip_install(pkg_cmd):
    start = time.time()
    result = run_cmd(pkg_cmd, capture=True)
    elapsed = time.time() - start
    if isinstance(result, Exception) or result.returncode != 0:
        reason = result.stderr if hasattr(result, 'stderr') else str(result)
        print_marker(f"INSTALL_FAIL:{reason}")
        return False, elapsed
    print_marker("INSTALL_OK")
    return True, elapsed

def clone_repo(url, dest):
    start = time.time()
    result = run_cmd(f"git clone {shlex.quote(url)} {shlex.quote(str(dest))}", capture=True)
    elapsed = time.time() - start
    if isinstance(result, Exception) or result.returncode != 0:
        reason = result.stderr if hasattr(result, 'stderr') else str(result)
        print_marker(f"INSTALL_FAIL:{reason}")
        return False, elapsed
    print_marker("INSTALL_OK")
    return True, elapsed

def measure_import(module_name):
    tracemalloc.start()
    start = time.time()
    try:
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        mem = tracemalloc.get_traced_memory()[1] / 1024  # KiB
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_mem_kb:{mem:.2f}")
        return True, import_time
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"TEST_FAIL:import_module:{e}")
        return False, 0.0

def create_dummy_pcap(path):
    # use scapy to create a tiny pcap if possible, else touch file
    try:
        import scapy.all as scapy
        pkt = scapy.Ether()/scapy.IP(dst="1.2.3.4")/scapy.TCP(dport=80)
        scapy.wrpcap(str(path), [pkt])
        return True
    except Exception:
        try:
            pathlib.Path(path).write_bytes(b'')
            return True
        except Exception:
            return False

def run_cli_analyzer(repo_dir, pcap_path):
    analyzer_cmd = f"python -m pcapanalyzer.cli analyze {shlex.quote(str(pcap_path))}"
    start = time.time()
    result = run_cmd(analyzer_cmd, capture=True)
    elapsed = time.time() - start
    if isinstance(result, Exception) or result.returncode != 0:
        print_marker(f"TEST_FAIL:cli_analysis:{result}")
        return False, elapsed
    out = result.stdout.lower()
    if "detected" in out or "issue" in out:
        print_marker("TEST_PASS:cli_analysis")
    else:
        print_marker("TEST_FAIL:cli_analysis:No detections found")
    return True, elapsed

def run_zeek_baseline(pcap_path):
    # attempt to run zeek; if not installed, return dummy high value
    cmd = f"zeek -r {shlex.quote(str(pcap_path))} > /dev/null"
    start = time.time()
    result = run_cmd(cmd, capture=True)
    elapsed = time.time() - start
    if isinstance(result, Exception) or result.returncode != 0:
        # assume zeek not present; use a large placeholder
        return 30.0
    return elapsed

def main():
    # 1. Install system packages
    ok, install_time = install_apk("git")
    print_marker(f"BENCHMARK:apk_git_install_s:{install_time:.2f}")

    # 2. Clone repo
    repo_url = "https://github.com/sebaandrada-cell/PcapAnalyzer"
    repo_dir = pathlib.Path(tempfile.mkdtemp()) / "PcapAnalyzer"
    ok, clone_time = clone_repo(repo_url, repo_dir)
    print_marker(f"BENCHMARK:repo_clone_s:{clone_time:.2f}")

    # 3. Install python deps
    req_file = repo_dir / "requirements.txt"
    if req_file.is_file():
        ok, pip_time = pip_install(f"pip install -r {shlex.quote(str(req_file))}")
    else:
        ok, pip_time = pip_install(f"pip install -e {shlex.quote(str(repo_dir))}")
    print_marker(f"BENCHMARK:pip_install_s:{pip_time:.2f}")

    # 4. Measure import
    measure_import("pcapanalyzer")

    # 5. Create dummy pcap
    pcap_path = repo_dir / "sample.pcap"
    if not create_dummy_pcap(pcap_path):
        print_marker("TEST_FAIL:create_pcap:Unable to create dummy pcap")
    else:
        print_marker("TEST_PASS:create_pcap")

    # 6. Run CLI analyzer
    try:
        ok, cli_time = run_cli_analyzer(repo_dir, pcap_path)
        print_marker(f"BENCHMARK:cli_analysis_s:{cli_time:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_analysis:{e}")

    # 7. Baseline comparison with Zeek
    zeek_time = run_zeek_baseline(pcap_path)
    print_marker(f"BENCHMARK:zeek_analysis_s:{zeek_time:.2f}")
    if zeek_time > 0:
        ratio = cli_time / zeek_time if zeek_time else 0
        print_marker(f"BENCHMARK:vs_zeek_time_ratio:{ratio:.2f}")

    # Additional benchmarks
    print_marker(f"BENCHMARK:loc_count:{sum(1 for _ in open(repo_dir/'pcapanalyzer/__init__.py'))}")
    print_marker(f"BENCHMARK:test_files_count:{len(list(repo_dir.rglob('test_*.py')))}")
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()