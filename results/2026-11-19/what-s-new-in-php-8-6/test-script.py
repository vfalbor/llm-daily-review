#!/usr/bin/env python3
import subprocess, sys, time, os, tracemalloc, json, shlex, re, pathlib, tempfile

def print_marker(line):
    print(line, flush=True)

def run_cmd(cmd, cwd=None, env=None, capture=False):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=True,
        )
        return (0, result.stdout if capture else "", result.stderr if capture else "")
    except subprocess.CalledProcessError as e:
        return (e.returncode, e.stdout if capture else "", e.stderr if capture else "")

def apk_install(pkgs):
    start = time.time()
    ret, _, err = run_cmd(['apk', 'add', '--no-cache'] + pkgs)
    elapsed = time.time() - start
    if ret == 0:
        print_marker(f"INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{err.strip() or 'apk install error'}")
    print_marker(f"BENCHMARK:apk_install_time_s:{elapsed:.2f}")
    return ret == 0

def git_clone(repo, dest):
    start = time.time()
    ret, _, err = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    elapsed = time.time() - start
    if ret == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:git clone error: {err.strip()}")
    print_marker(f"BENCHMARK:git_clone_time_s:{elapsed:.2f}")
    return ret == 0

def measure(func):
    """Decorator to measure execution time and memory."""
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        start = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
            err = ""
        except Exception as e:
            result = None
            success = False
            err = str(e)
        elapsed = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return success, result, err, elapsed, peak / 1024  # KiB
    return wrapper

@measure
def compile_php(src_dir, build_dir):
    os.makedirs(build_dir, exist_ok=True)
    # Configure
    ret, _, err = run_cmd(['./buildconf', '--force'], cwd=src_dir)
    if ret != 0:
        raise RuntimeError(f"buildconf failed: {err}")
    ret, _, err = run_cmd(['./configure', '--disable-all', '--enable-cli'], cwd=src_dir)
    if ret != 0:
        raise RuntimeError(f"configure failed: {err}")
    # Make
    ret, _, err = run_cmd(['make', '-j', str(os.cpu_count())], cwd=src_dir)
    if ret != 0:
        raise RuntimeError(f"make failed: {err}")
    # php binary will be at src_dir/sapi/cli/php
    php_path = os.path.join(src_dir, 'sapi', 'cli', 'php')
    if not os.path.isfile(php_path):
        raise RuntimeError("php binary not found after build")
    return php_path

@measure
def run_php_version(php_bin):
    ret, out, err = run_cmd([php_bin, '-v'], capture=True)
    if ret != 0:
        raise RuntimeError(f"php -v failed: {err}")
    return out.strip()

@measure
def run_php_script(php_bin, script):
    ret, out, err = run_cmd([php_bin, '-r', script], capture=True)
    if ret != 0:
        raise RuntimeError(f"php -r failed: {err}")
    return out.strip()

def main():
    # 1. Install required system packages
    apk_packages = ['go', 'git', 'cargo', 'rust', 'nodejs', 'npm', 'autoconf', 'bison', 're2c', 'libxml2-dev', 'openssl-dev', 'zlib-dev', 'sqlite-dev', 'oniguruma-dev', 'curl-dev']
    apk_install(apk_packages)

    work_dir = pathlib.Path(tempfile.mkdtemp(prefix="php_test_"))
    src_dir = work_dir / "php-src"
    build_dir = work_dir / "build"

    # 2. Clone repository
    repo_url = "https://github.com/php/php-src"
    if not git_clone(repo_url, str(src_dir)):
        print_marker("TEST_FAIL:clone_repo:git clone failed")
        print_marker("RUN_OK")
        return

    # 3. Compile PHP
    compile_success, php_path, err, compile_time, compile_mem = compile_php(str(src_dir), str(build_dir))
    if compile_success:
        print_marker(f"TEST_PASS:compile_php")
        print_marker(f"BENCHMARK:compile_time_s:{compile_time:.2f}")
        print_marker(f"BENCHMARK:compile_mem_kib:{compile_mem:.1f}")
    else:
        print_marker(f"TEST_FAIL:compile_php:{err}")

    # 4. Verify php -v
    version_success, version_out, err, ver_time, ver_mem = run_php_version(php_path)
    if version_success:
        if re.search(r'PHP\s+8\.6', version_out):
            print_marker("TEST_PASS:php_version")
        else:
            print_marker(f"TEST_FAIL:php_version:unexpected version output {version_out}")
        print_marker(f"BENCHMARK:php_version_time_s:{ver_time:.3f}")
    else:
        print_marker(f"TEST_FAIL:php_version:{err}")

    # 5. Run simple hello script via -r
    hello_success, hello_out, err, hello_time, hello_mem = run_php_script(php_path, "echo 'hello';")
    if hello_success:
        if hello_out == 'hello':
            print_marker("TEST_PASS:hello_cli")
        else:
            print_marker(f"TEST_FAIL:hello_cli:output mismatch {hello_out}")
        print_marker(f"BENCHMARK:hello_cli_time_s:{hello_time:.4f}")
    else:
        print_marker(f"TEST_FAIL:hello_cli:{err}")

    # 6. Benchmark script (loop)
    bench_script = """
$start = microtime(true);
for ($i=0;$i<100000;$i++) { $a = $i*$i; }
echo microtime(true)-$start;
"""
    bench_success, bench_out, err, bench_time, bench_mem = run_php_script(php_path, bench_script)
    if bench_success:
        try:
            exec_time = float(bench_out)
            print_marker(f"TEST_PASS:benchmark_loop")
            print_marker(f"BENCHMARK:benchmark_loop_seconds:{exec_time:.4f}")
        except:
            print_marker(f"TEST_FAIL:benchmark_loop:could not parse output {bench_out}")
    else:
        print_marker(f"TEST_FAIL:benchmark_loop:{err}")

    # 7. Compare vs baseline (Python 3.12) for same loop
    def python_loop():
        start = time.time()
        for i in range(100000):
            a = i*i
        return time.time() - start

    py_time = python_loop()
    if bench_success:
        ratio = bench_time / py_time if py_time else 0
        print_marker(f"BENCHMARK:vs_python_loop_ratio:{ratio:.3f}")

    # Ensure at least 3 benchmark lines (we have many)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()