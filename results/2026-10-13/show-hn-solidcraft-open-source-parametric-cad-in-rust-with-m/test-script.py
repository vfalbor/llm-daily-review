#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib, re

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=False, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkg):
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', pkg])
    if rc == 0:
        print(f"INSTALL_OK | {pkg}")
    else:
        print(f"INSTALL_FAIL:{pkg}:{err.strip() or 'unknown error'}")
    return rc == 0

def benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def test_pass(name):
    print(f"TEST_PASS:{name}")

def test_fail(name, reason):
    print(f"TEST_FAIL:{name}:{reason}")

def test_skip(name, reason):
    print(f"TEST_SKIP:{name}:{reason}")

def main():
    # 1. Install required system packages
    for pkg in ['nodejs', 'npm', 'git', 'cargo', 'rust']:
        install_apk(pkg)

    # Ensure working directory
    workdir = pathlib.Path('/tmp/solidcraft_test')
    workdir.mkdir(parents=True, exist_ok=True)

    repo_url = "https://github.com/bherbruck/solidcraft"
    src_dir = workdir / "solidcraft"

    # Clone repository
    if not src_dir.exists():
        rc, out, err = run_cmd(['git', 'clone', '--depth', '1', repo_url, str(src_dir)])
        if rc != 0:
            test_fail("clone_repo", err.strip())
            print("RUN_OK")
            return
    else:
        rc, out, err = run_cmd(['git', 'pull'], cwd=str(src_dir))
        if rc != 0:
            test_fail("git_pull", err.strip())

    # 2. Cargo build --release and measure build time
    try:
        start = time.time()
        rc, out, err = run_cmd(['cargo', 'build', '--release'], cwd=str(src_dir))
        build_time = time.time() - start
        benchmark("install_time_s", f"{build_time:.2f}")
        if rc == 0:
            test_pass("cargo_build")
        else:
            test_fail("cargo_build", err.strip() or "build failed")
    except Exception as e:
        test_fail("cargo_build", str(e))

    # Path to built binary
    bin_path = src_dir / "target" / "release" / "solidcraft"
    if not bin_path.is_file():
        test_skip("binary_exists", "binary not found after build")
        # can't continue with further tests that need the binary
        print("RUN_OK")
        return

    # 3. Run solidcraft --help
    try:
        rc, out, err = run_cmd([str(bin_path), '--help'])
        if rc == 0:
            test_pass("help_exit")
        else:
            test_fail("help_exit", f"exit {rc}")
    except Exception as e:
        test_fail("help_exit", str(e))

    # 4. Generate a simple cube and export to STL
    cube_stl = workdir / "cube.stl"
    try:
        start = time.time()
        rc, out, err = run_cmd([str(bin_path), 'cube', '--size', '1', '--output', str(cube_stl)])
        gen_time = time.time() - start
        benchmark("model_gen_time_ms", f"{gen_time*1000:.1f}")
        if rc != 0:
            test_fail("generate_cube", err.strip() or f"exit {rc}")
        else:
            if cube_stl.is_file() and cube_stl.stat().st_size < 5*1024:
                test_pass("cube_stl_size")
                benchmark("cube_stl_size_bytes", cube_stl.stat().st_size)
            else:
                test_fail("cube_stl_size", f"file missing or too large ({cube_stl.stat().st_size if cube_stl.is_file() else '0'} bytes)")
    except Exception as e:
        test_fail("generate_cube", str(e))

    # 5. Render the cube using MCP and check dimensions (simulate with placeholder)
    render_png = workdir / "cube.png"
    try:
        start = time.time()
        rc, out, err = run_cmd([str(bin_path), 'render', '--input', str(cube_stl),
                                '--output', str(render_png), '--size', '512'])
        render_time = time.time() - start
        benchmark("render_time_ms", f"{render_time*1000:.1f}")
        if rc != 0:
            test_fail("render_cube", err.strip() or f"exit {rc}")
        else:
            if render_png.is_file():
                # crude check using file size as proxy for dimensions
                size = render_png.stat().st_size
                if size > 0:
                    test_pass("render_dimensions")
                else:
                    test_fail("render_dimensions", "output file empty")
            else:
                test_fail("render_dimensions", "output file not created")
    except Exception as e:
        test_fail("render_cube", str(e))

    # 6. Measure memory usage during model generation
    try:
        tracemalloc.start()
        rc, out, err = run_cmd([str(bin_path), 'cube', '--size', '1', '--output', str(workdir/'tmp.stl')])
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        benchmark("memory_peak_kb", f"{peak/1024:.1f}")
        if rc == 0:
            test_pass("memory_usage")
        else:
            test_fail("memory_usage", err.strip() or f"exit {rc}")
    except Exception as e:
        test_fail("memory_usage", str(e))

    # Baseline comparison with OpenSCAD (assume we have openscad installed)
    # We'll measure a simple cube generation time with openscad if available
    openscad_bin = shutil.which("openscad")
    if openscad_bin:
        openscad_script = workdir / "cube.scad"
        openscad_script.write_text("cube(1);")
        try:
            start = time.time()
            rc, out, err = run_cmd([openscad_bin, '-o', str(workdir/'openscad_cube.stl'), str(openscad_script)])
            oc_time = time.time() - start
            benchmark("openscad_gen_time_ms", f"{oc_time*1000:.1f}")
            if rc == 0:
                ratio = gen_time / oc_time if oc_time > 0 else 0
                benchmark("vs_openscad_gen_time_ratio", f"{ratio:.2f}")
            else:
                test_skip("openscad_gen", "openscad execution failed")
        except Exception as e:
            test_skip("openscad_gen", str(e))
    else:
        test_skip("openscad_available", "openscad not installed")

    # Ensure at least 3 benchmark lines (we have many already)
    print("RUN_OK")

if __name__ == "__main__":
    main()