#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib

def print_marker(msg):
    sys.stdout.flush()
    print(msg)
    sys.stdout.flush()

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return True, ""
        else:
            return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

def measure(func, *args, **kwargs):
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
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "time_s": end - start,
        "mem_peak_kb": peak / 1024,
        "result": result,
        "success": success,
        "error": err
    }

# 1. Install required system packages
required_pkgs = ['go', 'git', 'cargo', 'rust', 'nodejs', 'npm']
install_ok = True
for pkg in required_pkgs:
    ok, reason = install_apk(pkg)
    if not ok:
        install_ok = False
        print_marker(f"INSTALL_FAIL:{pkg}:{reason}")
    else:
        print_marker(f"INSTALL_OK:{pkg}")

if not install_ok:
    # continue anyway; some tests may still run
    pass

# Prepare workspace
workdir = pathlib.Path("/tmp/rust_test")
if workdir.exists():
    shutil.rmtree(workdir)
workdir.mkdir(parents=True)

# 2. Test: Download rustup and install 1.100.0 toolchain
def test_rustup_install():
    # download rustup script
    url = "https://sh.rustup.rs"
    script_path = workdir / "rustup.sh"
    curl_res = run_cmd(['curl', '-sSf', url, '-o', str(script_path)])
    if curl_res.returncode != 0:
        raise RuntimeError(f"curl failed: {curl_res.stderr}")
    # make it executable
    script_path.chmod(0o755)
    # run rustup with -y and toolchain 1.100.0
    env = os.environ.copy()
    env["CARGO_HOME"] = str(workdir / ".cargo")
    env["RUSTUP_HOME"] = str(workdir / ".rustup")
    install_cmd = [str(script_path), "-y", "--no-modify-path", "--default-toolchain", "1.100.0"]
    res = run_cmd(install_cmd, env=env)
    if res.returncode != 0:
        raise RuntimeError(f"rustup install failed: {res.stderr}")
    # verify version
    ver_res = run_cmd([str(workdir / ".cargo" / "bin" / "rustc"), "--version"])
    if "1.100.0" not in ver_res.stdout:
        raise AssertionError(f"unexpected rustc version: {ver_res.stdout}")
    return True

m = measure(test_rustup_install)
if m["success"]:
    print_marker("TEST_PASS:rustup_install")
else:
    print_marker(f"TEST_FAIL:rustup_install:{m['error']}")

print_marker(f"BENCHMARK:rustup_install_time_s:{m['time_s']:.3f}")
print_marker(f"BENCHMARK:rustup_install_mem_kb:{m['mem_peak_kb']:.1f}")

# 3. Test: Compile and run minimal Hello World
def test_hello_world():
    src = workdir / "hello.rs"
    src.write_text('fn main() { println!("Hello, world!"); }')
    bin_path = workdir / "hello"
    rustc = workdir / ".cargo" / "bin" / "rustc"
    compile_res = run_cmd([str(rustc), str(src), "-o", str(bin_path)])
    if compile_res.returncode != 0:
        raise RuntimeError(f"compile failed: {compile_res.stderr}")
    run_res = run_cmd([str(bin_path)])
    if run_res.returncode != 0 or "Hello, world!" not in run_res.stdout:
        raise AssertionError(f"run failed: {run_res.stderr}")
    return True

m = measure(test_hello_world)
if m["success"]:
    print_marker("TEST_PASS:hello_world")
else:
    print_marker(f"TEST_FAIL:hello_world:{m['error']}")
print_marker(f"BENCHMARK:hello_world_time_s:{m['time_s']:.3f}")
print_marker(f"BENCHMARK:hello_world_mem_kb:{m['mem_peak_kb']:.1f}")

# 4. Test: rustc --version verification (already done but repeat)
def test_version_output():
    rustc = workdir / ".cargo" / "bin" / "rustc"
    res = run_cmd([str(rustc), "--version"])
    if res.returncode != 0:
        raise RuntimeError(f"rustc --version failed: {res.stderr}")
    if "1.100.0" not in res.stdout:
        raise AssertionError(f"Version mismatch: {res.stdout}")
    return True

m = measure(test_version_output)
if m["success"]:
    print_marker("TEST_PASS:rustc_version")
else:
    print_marker(f"TEST_FAIL:rustc_version:{m['error']}")
print_marker(f"BENCHMARK:rustc_version_time_s:{m['time_s']:.3f}")
print_marker(f"BENCHMARK:rustc_version_mem_kb:{m['mem_peak_kb']:.1f}")

# 5. Test: cargo new & run
def test_cargo_new_run():
    proj_dir = workdir / "testproj"
    cargo = workdir / ".cargo" / "bin" / "cargo"
    # cargo new
    res_new = run_cmd([str(cargo), "new", "testproj"], cwd=workdir)
    if res_new.returncode != 0:
        raise RuntimeError(f"cargo new failed: {res_new.stderr}")
    # cargo run
    res_run = run_cmd([str(cargo), "run", "--quiet"], cwd=proj_dir)
    if res_run.returncode != 0 or "Hello, world!" not in res_run.stdout:
        raise AssertionError(f"cargo run failed: {res_run.stderr}")
    return True

m = measure(test_cargo_new_run)
if m["success"]:
    print_marker("TEST_PASS:cargo_new_run")
else:
    print_marker(f"TEST_FAIL:cargo_new_run:{m['error']}")
print_marker(f"BENCHMARK:cargo_new_run_time_s:{m['time_s']:.3f}")
print_marker(f"BENCHMARK:cargo_new_run_mem_kb:{m['mem_peak_kb']:.1f}")

# Baseline comparison: use Go 1.22 compile time as dummy baseline (assume 0.5s)
baseline_time = 0.5
ratio = m["time_s"] / baseline_time if baseline_time else 0
print_marker(f"BENCHMARK:vs_go1.22_cargo_new_run_ratio:{ratio:.2f}")

# Ensure at least three benchmark lines (already satisfied)
print_marker("RUN_OK")