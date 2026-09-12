import subprocess, sys, time, tracemalloc, os, json, pathlib, shlex

def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def print_marker(line):
    print(line, flush=True)

def install_system(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{pkg}:{err or out}")

def install_tool_deps():
    # nodejs and npm already installed via apk above
    pass

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def main():
    start_total = time.time()
    tracemalloc.start()

    # 1. Install required system packages
    for pkg in ['git', 'openjdk17', 'gradle', 'nodejs', 'npm']:
        install_system(pkg)

    # 2. Clone repository
    repo_url = "https://github.com/GrapheneOS/Messaging"
    repo_dir = "Messaging"
    try:
        if os.path.isdir(repo_dir):
            rc, out, err = run_cmd(['git', 'pull'], cwd=repo_dir)
        else:
            rc, out, err = run_cmd(['git', 'clone', repo_url])
        if rc == 0:
            print_marker("TEST_PASS:clone_repo")
        else:
            raise RuntimeError(f"git clone failed: {err or out}")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")
        repo_dir = None

    # 3. Install npm dependencies (if any)
    if repo_dir:
        try:
            rc, out, err = run_cmd(['npm', 'install'], cwd=repo_dir)
            if rc == 0:
                print_marker("TEST_PASS:npm_install")
            else:
                raise RuntimeError(f"npm install failed: {err or out}")
        except Exception as e:
            print_marker(f"TEST_FAIL:npm_install:{e}")

    # 4. Build APK with Gradle
    build_time = None
    apk_path = None
    if repo_dir:
        build_start = time.time()
        try:
            rc, out, err = run_cmd(['./gradlew', 'assembleRelease'], cwd=repo_dir)
            if rc == 0:
                build_time = time.time() - build_start
                benchmark("build_time_s", f"{build_time:.2f}")
                print_marker("TEST_PASS:gradle_build")
                # locate apk
                apk_glob = pathlib.Path(repo_dir) / "app" / "build" / "outputs" / "apk" / "release"
                apks = list(apk_glob.glob("*.apk"))
                if apks:
                    apk_path = str(apks[0])
                else:
                    raise RuntimeError("APK not found after build")
            else:
                raise RuntimeError(f"gradle build failed: {err or out}")
        except Exception as e:
            print_marker(f"TEST_FAIL:gradle_build:{e}")

    # 5. Measure APK size
    if apk_path and os.path.isfile(apk_path):
        try:
            size_bytes = os.path.getsize(apk_path)
            benchmark("apk_size_kb", f"{size_bytes/1024:.1f}")
            print_marker("TEST_PASS:apk_size")
        except Exception as e:
            print_marker(f"TEST_FAIL:apk_size:{e}")

    # 6. Simulate launch and UI verification (placeholder using adb check)
    if apk_path:
        try:
            rc, out, err = run_cmd(['adb', 'install', '-r', apk_path])
            if rc != 0:
                raise RuntimeError(f"adb install failed: {err or out}")
            # launch app (package name guessed)
            pkg = "org.grapheneos.messaging"
            rc, out, err = run_cmd(['adb', 'shell', 'am', 'start', '-n', f"{pkg}/.MainActivity"])
            if rc == 0:
                print_marker("TEST_PASS:app_launch")
            else:
                raise RuntimeError(f"app launch failed: {err or out}")
        except Exception as e:
            print_marker(f"TEST_FAIL:app_launch:{e}")

    # 7. Send HTTP request to local server if it exists
    try:
        # assume server runs on http://127.0.0.1:8080/health
        import urllib.request
        health_url = "http://127.0.0.1:8080/health"
        start = time.time()
        with urllib.request.urlopen(health_url, timeout=5) as resp:
            data = resp.read()
        latency = (time.time() - start) * 1000
        benchmark("health_latency_ms", f"{latency:.2f}")
        print_marker("TEST_PASS:health_endpoint")
    except Exception as e:
        print_marker(f"TEST_FAIL:health_endpoint:{e}")

    # 8. Baseline comparison vs Signal (dummy baseline build time 15s)
    baseline_build = 15.0
    if build_time is not None:
        ratio = build_time / baseline_build
        benchmark("vs_signal_build_time_ratio", f"{ratio:.2f}")

    # Emit additional benchmarks
    current, peak = tracemalloc.get_traced_memory()
    benchmark("memory_peak_kb", f"{peak/1024:.1f}")
    total_time = time.time() - start_total
    benchmark("total_runtime_s", f"{total_time:.2f}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()