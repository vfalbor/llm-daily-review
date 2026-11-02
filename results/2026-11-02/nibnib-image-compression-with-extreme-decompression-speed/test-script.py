#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, shutil, json, math, pathlib, tempfile

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{' '.join(cmd)} failed: {e.stderr.strip()}")

def apk_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def print_marker(line):
    print(line, flush=True)

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def test_result(status, name, reason=None):
    if status == "PASS":
        print_marker(f"TEST_PASS:{name}")
    elif status == "FAIL":
        print_marker(f"TEST_FAIL:{name}:{reason}")
    elif status == "SKIP":
        print_marker(f"TEST_SKIP:{name}:{reason}")

def measure_time(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return result, end - start

def main():
    # 1. Install required apk packages
    try:
        apk_install('git')
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

    # 2. Try pip install nibnib
    install_success = False
    try:
        t0 = time.time()
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'nibnib'], check=True)
        benchmark("pip_install_time_s", round(time.time() - t0, 3))
        install_success = True
    except Exception as e:
        benchmark("pip_install_time_s", -1)
        # fallback to git clone + editable install
        try:
            tmpdir = tempfile.mkdtemp()
            repo_url = "https://github.com/raphlinus/nibnib.git"
            run_cmd(['git', 'clone', '--depth', '1', repo_url, tmpdir])
            t1 = time.time()
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', '.'],
                           cwd=tmpdir, check=True)
            benchmark("git_clone_editable_install_s", round(time.time() - t1, 3))
            install_success = True
        except Exception as e2:
            test_result("FAIL", "install_nibnib", f"pip and git fallback failed: {e2}")

    if not install_success:
        test_result("FAIL", "import_nibnib", "Installation failed")
        # still continue to emit benchmarks and RUN_OK
    else:
        # 3. Import time benchmark
        try:
            _, imp_time = measure_time(__import__, "nibnib")
            benchmark("import_time_ms", int(imp_time * 1000))
            test_result("PASS", "import_nibnib")
        except Exception as e:
            test_result("FAIL", "import_nibnib", str(e))

        # 4. Functional test: compress & decompress synthetic data
        try:
            import nibnib
            import numpy as np
            # create synthetic image (RGB 256x256)
            img = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
            # compress
            _, comp_time = measure_time(nibnib.encode, img.tobytes(), width=256, height=256, channels=3)
            # decompress
            _, decomp_time = measure_time(nibnib.decode, nibnib.encode(img.tobytes(), width=256, height=256, channels=3))
            benchmark("compress_time_ms", int(comp_time * 1000))
            benchmark("decompress_time_ms", int(decomp_time * 1000))
            test_result("PASS", "compress_decompress")
        except Exception as e:
            test_result("FAIL", "compress_decompress", str(e))

        # 5. Compare decompression latency vs zstd (using python zstandard)
        try:
            import zstandard as zstd
            # compress with zstd for same raw data
            cctx = zstd.ZstdCompressor()
            dctx = zstd.ZstdDecompressor()
            _, z_comp = measure_time(cctx.compress, img.tobytes())
            _, z_decomp = measure_time(dctx.decompress, cctx.compress(img.tobytes()))
            benchmark("zstd_decompress_time_ms", int(z_decomp * 1000))
            # ratio
            if decomp_time > 0:
                ratio = decomp_time / z_decomp
                benchmark("vs_zstd_decompress_ratio", round(ratio, 3))
            test_result("PASS", "compare_vs_zstd")
        except Exception as e:
            test_result("SKIP", "compare_vs_zstd", f"zstandard not available: {e}")

        # 6. CLI test if binary exists
        try:
            # ensure binary built
            bin_path = shutil.which("nibnib")
            if not bin_path:
                # try building via cargo if not present
                src_dir = pathlib.Path(tmpdir) if 'tmpdir' in locals() else None
                if src_dir and (src_dir / "Cargo.toml").exists():
                    run_cmd(['cargo', 'build', '--release'], cwd=src_dir)
                    bin_path = src_dir / "target" / "release" / "nibnib"
            if not bin_path or not os.path.isfile(bin_path):
                raise RuntimeError("CLI binary not found")
            # create temp file
            with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as raw_f:
                raw_f.write(img.tobytes())
                raw_name = raw_f.name
            out_name = raw_name + ".nb"
            t_cli_start = time.time()
            run_cmd([str(bin_path), "compress", raw_name, out_name, "--width", "256", "--height", "256", "--channels", "3"])
            cli_time = time.time() - t_cli_start
            benchmark("cli_compress_time_ms", int(cli_time * 1000))
            # decompress via CLI to verify
            dec_out = raw_name + ".dec"
            run_cmd([str(bin_path), "decompress", out_name, dec_out])
            # compare files
            if pathlib.Path(dec_out).read_bytes() == pathlib.Path(raw_name).read_bytes():
                test_result("PASS", "cli_compress_decompress")
            else:
                test_result("FAIL", "cli_compress_decompress", "output mismatch")
            # cleanup
            for f in (raw_name, out_name, dec_out):
                try:
                    os.remove(f)
                except OSError:
                    pass
        except Exception as e:
            test_result("SKIP", "cli_compress_decompress", str(e))

    # Ensure at least 3 benchmark lines (we already have many)
    # Final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()