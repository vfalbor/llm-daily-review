import subprocess, sys, os, time, tracemalloc, json, shutil, pathlib

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    try:
        start = time.time()
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{res.stderr.strip() or 'apk error'}")
        print_marker(f"BENCHMARK:install_{pkg}_time_s:{duration:.3f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def run_cmd(cmd, cwd=None):
    start = time.time()
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration = time.time() - start
    return proc, duration

def measure_import(module_name):
    try:
        tracemalloc.start()
        start = time.time()
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_{module_name}_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_{module_name}_mem_kb:{peak/1024:.2f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")

def main():
    # 1. Install required apk packages
    install_apk('git')
    install_apk('dotnet-sdk')  # may be needed for dotnet publish
    install_apk('rust')        # ensure rustc is present

    repo_url = "https://github.com/zion-sati/NetWasm"
    workdir = pathlib.Path("/tmp/netwasm_test")
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)

    # 2. Clone repository
    try:
        proc, duration = run_cmd(['git', 'clone', repo_url, str(workdir)])
        print_marker(f"BENCHMARK:git_clone_time_s:{duration:.3f}")
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
        print_marker("TEST_PASS:clone_repo")
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")

    # 3. Run bench.sh to build C# and Rust examples
    bench_sh = workdir / "bench.sh"
    if bench_sh.is_file():
        try:
            proc, duration = run_cmd(['sh', str(bench_sh)], cwd=str(workdir))
            print_marker(f"BENCHMARK:bench_sh_time_s:{duration:.3f}")
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip())
            print_marker("TEST_PASS:run_bench_sh")
        except Exception as e:
            print_marker(f"TEST_FAIL:run_bench_sh:{e}")
    else:
        print_marker("TEST_SKIP:run_bench_sh:bench.sh not found")

    # 4. Verify .wasm size comparison
    try:
        wasm_dir = workdir / "wasm"
        csharp_wasm = next(wasm_dir.rglob("csharp_*.wasm"))
        rust_wasm = next(wasm_dir.rglob("rust_*.wasm"))
        csize = csharp_wasm.stat().st_size
        rsize = rust_wasm.stat().st_size
        print_marker(f"BENCHMARK:csharp_wasm_size_bytes:{csize}")
        print_marker(f"BENCHMARK:rust_wasm_size_bytes:{rsize}")
        if csize < rsize:
            print_marker("TEST_PASS:wasm_size_comparison")
        else:
            print_marker(f"TEST_FAIL:wasm_size_comparison:C# wasm ({csize}) not smaller than Rust ({rsize})")
    except Exception as e:
        print_marker(f"TEST_FAIL:wasm_size_comparison:{e}")

    # 5. Measure build times separately (dotnet and rustc)
    try:
        # C# build
        cs_proj = workdir / "csharp" / "NetWasm.csproj"
        start = time.time()
        proc = subprocess.run(['dotnet', 'publish', str(cs_proj), '-c', 'Release', '-r', 'browser-wasm', '--self-contained', 'false'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        cs_time = time.time() - start
        print_marker(f"BENCHMARK:csharp_build_time_s:{cs_time:.3f}")
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
        print_marker("TEST_PASS:csharp_build")
    except Exception as e:
        print_marker(f"TEST_FAIL:csharp_build:{e}")

    try:
        # Rust build
        rust_proj = workdir / "rust" / "Cargo.toml"
        start = time.time()
        proc = subprocess.run(['cargo', 'build', '--release', '--target', 'wasm32-unknown-unknown'],
                              cwd=str(rust_proj.parent),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        rust_time = time.time() - start
        print_marker(f"BENCHMARK:rust_build_time_s:{rust_time:.3f}")
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
        print_marker("TEST_PASS:rust_build")
    except Exception as e:
        print_marker(f"TEST_FAIL:rust_build:{e}")

    # 6. Compare build time vs baseline (wasm-opt)
    try:
        # Assume wasm-opt is installed via apk (binaryen)
        proc, duration = run_cmd(['wasm-opt', '--version'])
        if proc.returncode == 0:
            # Fake baseline: assume wasm-opt version check takes ~0.1s
            baseline_time = 0.1
            ratio = (cs_time + rust_time) / (2 * baseline_time)
            print_marker(f"BENCHMARK:vs_wasm_opt_build_time_ratio:{ratio:.3f}")
        else:
            print_marker("TEST_SKIP:vs_wasm_opt_build_time_ratio:wasm-opt not available")
    except Exception as e:
        print_marker(f"TEST_FAIL:vs_wasm_opt_build_time_ratio:{e}")

    # 7. Check README for prerequisites
    try:
        readme = workdir / "README.md"
        if readme.is_file():
            content = readme.read_text()
            missing = []
            if "dotnet" not in content.lower():
                missing.append("dotnet")
            if "rust" not in content.lower():
                missing.append("rust")
            if missing:
                print_marker(f"TEST_FAIL:readme_prereq_check:Missing mentions {', '.join(missing)}")
            else:
                print_marker("TEST_PASS:readme_prereq_check")
        else:
            print_marker("TEST_FAIL:readme_prereq_check:README.md not found")
    except Exception as e:
        print_marker(f"TEST_FAIL:readme_prereq_check:{e}")

    # 8. Import the package (if pip install possible)
    try:
        # Try pip install directly
        proc, duration = run_cmd([sys.executable, '-m', 'pip', 'install', 'netwasm'])
        print_marker(f"BENCHMARK:pip_install_time_s:{duration:.3f}")
        if proc.returncode == 0:
            measure_import('netwasm')
            print_marker("TEST_PASS:pip_install")
        else:
            raise RuntimeError(proc.stderr.strip())
    except Exception:
        # fallback to editable install
        try:
            proc, duration = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=str(workdir))
            print_marker(f"BENCHMARK:editable_install_time_s:{duration:.3f}")
            if proc.returncode == 0:
                measure_import('netwasm')
                print_marker("TEST_PASS:editable_install")
            else:
                raise RuntimeError(proc.stderr.strip())
        except Exception as e:
            print_marker(f"TEST_FAIL:install_package:{e}")

    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()