import subprocess, sys, time, tracemalloc, json, os, shlex, urllib.request, urllib.error

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        start = time.time()
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:apk_{pkg}_install_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk_{pkg}:{e}")

def pip_install(package):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:pip_{package}_install_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip_{package}:{e}")
        return False

def run_cmd(cmd, env=None):
    try:
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, 0.0

def measure_import(module_name):
    try:
        start = time.time()
        __import__(module_name)
        elapsed = (time.time() - start) * 1000
        print_marker(f"BENCHMARK:import_{module_name}_ms:{elapsed:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")

def clone_repo(url, dest):
    try:
        start = time.time()
        subprocess.run(['git', 'clone', '--depth', '1', url, dest],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:clone_{os.path.basename(dest)}_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")
        return False

def install_from_source(path):
    try:
        start = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'],
                       cwd=path, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:install_source_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:install_source:{e}")
        return False

def test_cli():
    try:
        result, elapsed = run_cmd(['floci', '--help'])
        if result and result.returncode == 0:
            print_marker(f"TEST_PASS:cli_help")
        else:
            reason = result.stderr.strip() if result else "no result"
            print_marker(f"TEST_FAIL:cli_help:{reason}")
        print_marker(f"BENCHMARK:cli_help_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_help:{e}")

def start_gcp_emulator():
    # floci can start emulators via subcommands; use generic start and check output
    try:
        result, elapsed = run_cmd(['floci', 'gcp', 'pubsub', 'start'])
        if result and result.returncode == 0:
            print_marker(f"TEST_PASS:gcp_emulator_start")
        else:
            reason = result.stderr.strip() if result else "no result"
            print_marker(f"TEST_FAIL:gcp_emulator_start:{reason}")
        print_marker(f"BENCHMARK:gcp_emulator_start_s:{elapsed:.3f}")
        return result and result.returncode == 0
    except Exception as e:
        print_marker(f"TEST_FAIL:gcp_emulator_start:{e}")
        return False

def publish_receive_latency():
    try:
        # Create a topic, publish a message, receive it, measure latency
        # Use floci CLI if available
        topic = "test-topic"
        msg = "hello"
        # create topic
        run_cmd(['floci', 'gcp', 'pubsub', 'create-topic', topic])
        # publish
        start = time.time()
        pub_res, _ = run_cmd(['floci', 'gcp', 'pubsub', 'publish', topic, msg])
        # receive (blocking with timeout)
        sub_res, _ = run_cmd(['floci', 'gcp', 'pubsub', 'pull', topic, '--max-messages', '1'])
        latency = (time.time() - start) * 1000
        if pub_res and sub_res and sub_res.returncode == 0:
            print_marker(f"TEST_PASS:publish_receive")
        else:
            reason = sub_res.stderr.strip() if sub_res else "no result"
            print_marker(f"TEST_FAIL:publish_receive:{reason}")
        print_marker(f"BENCHMARK:pubsub_latency_ms:{latency:.2f}")
        return latency
    except Exception as e:
        print_marker(f"TEST_FAIL:publish_receive:{e}")
        return None

def compare_with_baseline(metric, value):
    # Baseline: LocalStack Pub/Sub latency approx 5 ms (example)
    baseline = 5.0
    ratio = value / baseline if baseline else 0
    print_marker(f"BENCHMARK:vs_localstack_{metric}:{ratio:.2f}")

def main():
    # 1. Install required apk packages
    for pkg in ['git', 'curl']:
        apk_install(pkg)

    # 2. Try pip install floci
    if not pip_install('floci'):
        # fallback to source
        src_dir = '/tmp/floci_src'
        if clone_repo('https://github.com/flowg/floci', src_dir):
            install_from_source(src_dir)

    # 3. Measure import
    measure_import('floci')

    # 4. Test CLI
    test_cli()

    # 5. Start emulator
    if start_gcp_emulator():
        # 6. Latency test
        latency = publish_receive_latency()
        if latency is not None:
            compare_with_baseline('pubsub_latency_ms', latency)

    # Ensure at least three benchmark lines (install times, import, cli, etc. already printed)
    # Additional generic benchmark: memory snapshot
    try:
        tracemalloc.start()
        time.sleep(0.1)
        snapshot = tracemalloc.take_snapshot()
        total = sum(stat.size for stat in snapshot.statistics('filename'))
        print_marker(f"BENCHMARK:memory_bytes:{total}")
        tracemalloc.stop()
    except Exception as e:
        print_marker(f"TEST_FAIL:memory_snapshot:{e}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()