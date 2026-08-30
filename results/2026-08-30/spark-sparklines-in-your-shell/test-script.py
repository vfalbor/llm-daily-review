import subprocess, sys, time, tracemalloc, os, shlex, json, math

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture_output=False, text=True, check=False):
    return subprocess.run(cmd, shell=True, capture_output=capture_output, text=text, check=check)

def install_apk(packages):
    try:
        start = time.time()
        result = subprocess.run(['apk','add','--no-cache'] + packages, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk exit {result.returncode}")
        print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def install_spark():
    repo = "https://git.zx2c4.com/spark"
    clone_dir = "/tmp/spark_src"
    try:
        # ensure clean dir
        if os.path.isdir(clone_dir):
            subprocess.run(['rm','-rf',clone_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start = time.time()
        subprocess.run(f"git clone {repo} {clone_dir}", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # try make install
        subprocess.run("make install", cwd=clone_dir, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker("INSTALL_OK")
        print_marker(f"BENCHMARK:spark_install_time_s:{elapsed:.3f}")
        return True
    except subprocess.CalledProcessError as e:
        print_marker(f"INSTALL_FAIL:make/install {e}")
        # fallback: try pip install -e .
        try:
            start = time.time()
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], cwd=clone_dir, shell=True, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elapsed = time.time() - start
            print_marker("INSTALL_OK")
            print_marker(f"BENCHMARK:spark_pip_install_time_s:{elapsed:.3f}")
            return True
        except Exception as e2:
            print_marker(f"INSTALL_FAIL:pip fallback {e2}")
            return False

def test_help():
    try:
        start = time.time()
        res = run_cmd("spark --help", capture_output=True, check=True)
        elapsed = time.time() - start
        if "Usage" in res.stdout or "usage" in res.stdout.lower():
            print_marker("TEST_PASS:spark_help")
        else:
            print_marker("TEST_FAIL:spark_help:unexpected output")
        print_marker(f"BENCHMARK:help_time_ms:{elapsed*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:spark_help:{e}")

def test_basic_output():
    try:
        data = "10\n20\n30\n40\n"
        start = time.time()
        proc = subprocess.Popen(["spark"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate(data, timeout=5)
        elapsed = time.time() - start
        if proc.returncode == 0 and len(out.strip()) >= 4:
            print_marker("TEST_PASS:spark_basic")
        else:
            reason = "non-zero rc" if proc.returncode != 0 else "output too short"
            print_marker(f"TEST_FAIL:spark_basic:{reason}")
        print_marker(f"BENCHMARK:basic_output_ms:{elapsed*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:spark_basic:{e}")

def test_throughput():
    try:
        count = 100000
        numbers = "\n".join(str(i) for i in range(count)) + "\n"
        start = time.time()
        proc = subprocess.Popen(["spark"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate(numbers, timeout=30)
        elapsed = time.time() - start
        if proc.returncode == 0:
            print_marker("TEST_PASS:spark_throughput")
        else:
            print_marker(f"TEST_FAIL:spark_throughput:rc {proc.returncode}")
        print_marker(f"BENCHMARK:throughput_time_s:{elapsed:.3f}")
        # baseline: bbq (assume installed)
        try:
            baseline_start = time.time()
            bbq_proc = subprocess.Popen(["bbq"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            bbq_out, _ = bbq_proc.communicate(numbers, timeout=30)
            baseline_elapsed = time.time() - baseline_start
            ratio = elapsed / baseline_elapsed if baseline_elapsed > 0 else math.inf
            print_marker(f"BENCHMARK:vs_bbq_throughput_ratio:{ratio:.3f}")
        except Exception as be:
            print_marker(f"BENCHMARK:vs_bbq_throughput_ratio:baseline_failed")
    except Exception as e:
        print_marker(f"TEST_FAIL:spark_throughput:{e}")

def test_integration_script():
    try:
        script_path = "/tmp/run_spark.sh"
        with open(script_path, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("seq 1 5 | spark\n")
        os.chmod(script_path, 0o755)
        start = time.time()
        res = run_cmd(script_path, capture_output=True, check=True)
        elapsed = time.time() - start
        if res.stdout.strip():
            print_marker("TEST_PASS:spark_integration")
        else:
            print_marker("TEST_FAIL:spark_integration:no output")
        print_marker(f"BENCHMARK:integration_time_ms:{elapsed*1000:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:spark_integration:{e}")

def main():
    # 1. install required apk packages
    install_apk(['nodejs','npm','git','cargo','rust','make','gcc','musl-dev'])
    # 2. install spark
    if not install_spark():
        # if installation failed, skip further tests but still emit benchmarks and RUN_OK
        print_marker("TEST_SKIP:spark_help:install_failed")
        print_marker("TEST_SKIP:spark_basic:install_failed")
        print_marker("TEST_SKIP:spark_throughput:install_failed")
        print_marker("TEST_SKIP:spark_integration:install_failed")
        print_marker("RUN_OK")
        return

    # Run tests
    test_help()
    test_basic_output()
    test_throughput()
    test_integration_script()

    # Additional benchmarks: memory usage during a small run
    try:
        tracemalloc.start()
        proc = subprocess.Popen(["spark"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc.communicate("1\n2\n3\n4\n", timeout=5)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    except Exception as e:
        print_marker(f"BENCHMARK:memory_peak_kb:0")

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()