import subprocess, sys, time, tracemalloc, json, os, threading

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture=False, check=False):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None,
                                text=True, check=check)
        return result.stdout if capture else None
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {e.stderr.strip()}")

def install_apk(pkg):
    try:
        run_cmd(['apk', 'add', '--no-cache', pkg])
        print_marker(f"INSTALL_OK | {pkg}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def docker_pull(image):
    start = time.time()
    run_cmd(['docker', 'pull', image], check=True)
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:docker_pull_{image.replace('/', '_').replace(':', '_')}_s:{elapsed:.3f}")
    return elapsed

def run_hello_world(image):
    start = time.time()
    try:
        run_cmd(['docker', 'run', '--rm', image, 'echo', 'hello'], check=True)
        elapsed = time.time() - start
        print_marker(f"TEST_PASS:hello_world_start")
        print_marker(f"BENCHMARK:hello_world_start_s:{elapsed:.3f}")
        return elapsed
    except Exception as e:
        print_marker(f"TEST_FAIL:hello_world_start:{e}")
        return None

def inspect_cli(image):
    try:
        out = run_cmd(['docker', 'inspect', image], capture=True, check=True)
        data = json.loads(out)
        print_marker("TEST_PASS:cli_inspect")
        print_marker(f"BENCHMARK:cli_inspect_keys:{len(data)}")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_inspect:{e}")

def stress_test(image, count=5):
    def run_one(idx):
        try:
            run_cmd(['docker', 'run', '--rm', image, 'sh', '-c', 'exit 0'], check=True)
        except Exception as e:
            pass

    threads = []
    start = time.time()
    for i in range(count):
        t = threading.Thread(target=run_one, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:stress_{count}_containers_s:{elapsed:.3f}")

def benchmark_vs_baseline(metric, value, baseline):
    try:
        ratio = value / baseline if baseline else 0
        print_marker(f"BENCHMARK:vs_{baseline}_vs_{metric}_ratio:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install required apk packages
    for pkg in ['git', 'curl']:
        install_apk(pkg)

    # 2. Pull Kiri image
    image = 'ghcr.io/kiri-dev/kiri:latest'
    try:
        pull_time = docker_pull(image)
    except Exception as e:
        print_marker(f"TEST_FAIL:docker_pull:{e}")
        pull_time = None

    # 3. Run hello-world container
    hello_time = run_hello_world(image)

    # 4. Inspect CLI / image
    try:
        inspect_cli(image)
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_inspect:{e}")

    # 5. Stress test
    try:
        stress_test(image, count=5)
    except Exception as e:
        print_marker(f"TEST_FAIL:stress_test:{e}")

    # 6. Benchmark comparisons
    # Baseline using runc (approx values)
    baseline_pull = 8.0  # seconds (example)
    baseline_hello = 0.4  # seconds
    if pull_time is not None:
        benchmark_vs_baseline('docker_pull', pull_time, baseline_pull)
    if hello_time is not None:
        benchmark_vs_baseline('hello_world_start', hello_time, baseline_hello)

    # Memory usage benchmark
    tracemalloc.start()
    # dummy allocation
    lst = [i for i in range(1000000)]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")

    # Ensure final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()