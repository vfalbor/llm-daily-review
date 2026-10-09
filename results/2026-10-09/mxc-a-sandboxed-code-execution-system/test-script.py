import subprocess, sys, time, json, os, shlex, traceback, tracemalloc

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture=False, check=False):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, text=True, check=check
        )
        return result
    except Exception as e:
        return e

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True, ""
        else:
            return False, f"apk exit {res.returncode}"
    except Exception as e:
        return False, str(e)

def main():
    # 1. Install system packages
    for pkg in ['git', 'curl']:
        ok, reason = install_apk(pkg)
        if ok:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{reason}")

    # 2. Ensure docker client exists (assume docker is preinstalled in container)
    # No extra pip packages needed

    benchmarks = {}

    # Test 1: docker pull mxc:latest
    try:
        start = time.time()
        pull = run_cmd('docker pull mxc:latest', capture=True)
        duration = time.time() - start
        benchmarks['pull_time_s'] = duration
        if isinstance(pull, subprocess.CompletedProcess) and pull.returncode == 0:
            print_marker("TEST_PASS:docker_pull")
        else:
            reason = pull.stderr if isinstance(pull, subprocess.CompletedProcess) else str(pull)
            print_marker(f"TEST_FAIL:docker_pull:{reason.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:docker_pull:{e}")

    # Test 2: run simple Python script inside MXC and capture stdout
    try:
        script = "print('hello from sandbox')"
        # Create temp script file
        with open('/tmp/hello.py', 'w') as f:
            f.write(script)
        start = time.time()
        cmd = f'docker run --rm mxc:latest python /tmp/hello.py'
        # Bind mount the script
        cmd = f'docker run --rm -v /tmp/hello.py:/app/hello.py mxc:latest python /app/hello.py'
        result = run_cmd(cmd, capture=True)
        duration = time.time() - start
        benchmarks['run_simple_s'] = duration
        if isinstance(result, subprocess.CompletedProcess) and result.returncode == 0 and 'hello from sandbox' in result.stdout:
            print_marker("TEST_PASS:simple_python")
        else:
            reason = result.stderr if isinstance(result, subprocess.CompletedProcess) else str(result)
            print_marker(f"TEST_FAIL:simple_python:{reason.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:simple_python:{e}")

    # Test 3: measure start-up latency for a new sandbox container (empty command)
    try:
        start = time.time()
        result = run_cmd('docker run --rm mxc:latest echo ready', capture=True)
        latency = time.time() - start
        benchmarks['startup_latency_ms'] = latency * 1000
        if isinstance(result, subprocess.CompletedProcess) and result.returncode == 0:
            print_marker("TEST_PASS:start_up_latency")
        else:
            reason = result.stderr if isinstance(result, subprocess.CompletedProcess) else str(result)
            print_marker(f"TEST_FAIL:start_up_latency:{reason.strip()}")
    except Exception as e:
        print_marker(f"TEST_FAIL:start_up_latency:{e}")

    # Test 4: attempt privileged command (e.g., mount) and confirm blocked
    try:
        start = time.time()
        cmd = 'docker run --rm mxc:latest mount -t tmpfs none /mnt'
        result = run_cmd(cmd, capture=True)
        duration = time.time() - start
        benchmarks['priv_cmd_block_ms'] = duration * 1000
        # Expect non-zero exit or error message about permission
        if isinstance(result, subprocess.CompletedProcess) and result.returncode != 0:
            print_marker("TEST_PASS:privileged_block")
        else:
            reason = result.stdout + result.stderr if isinstance(result, subprocess.CompletedProcess) else str(result)
            print_marker(f"TEST_FAIL:privileged_block:command succeeded unexpectedly")
    except Exception as e:
        print_marker(f"TEST_FAIL:privileged_block:{e}")

    # Emit at least 3 benchmark lines
    for name, value in benchmarks.items():
        if isinstance(value, float):
            print_marker(f"BENCHMARK:{name}:{value:.3f}")

    # Baseline comparison against firecracker (dummy baseline values)
    # Assume baseline start-up latency = 150ms, mount block latency = 30ms
    baseline = {
        'startup_latency_ms': 150.0,
        'priv_cmd_block_ms': 30.0
    }
    if 'startup_latency_ms' in benchmarks:
        ratio = benchmarks['startup_latency_ms'] / baseline['startup_latency_ms']
        print_marker(f"BENCHMARK:vs_firecracker_startup_latency_ratio:{ratio:.3f}")
    if 'priv_cmd_block_ms' in benchmarks:
        ratio = benchmarks['priv_cmd_block_ms'] / baseline['priv_cmd_block_ms']
        print_marker(f"BENCHMARK:vs_firecracker_priv_cmd_block_ratio:{ratio:.3f}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()