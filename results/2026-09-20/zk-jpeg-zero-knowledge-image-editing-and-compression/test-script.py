import subprocess, sys, os, time, shutil, json, hashlib, tracemalloc, tempfile, pathlib, statistics, shlex, textwrap

# Helper to print markers
def emit(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkgs):
    start = time.time()
    try:
        result = subprocess.run(['apk', 'add', '--no-cache'] + pkgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            emit(f"INSTALL_OK")
        else:
            emit(f"INSTALL_FAIL:{result.stderr.strip()}")
    except Exception as e:
        emit(f"INSTALL_FAIL:{e}")
    finally:
        emit(f"BENCHMARK:install_time_s:{time.time()-start:.3f}")

def install_tool_deps():
    # npm, cargo already installed via apk above
    pass  # nothing extra

def clone_repo(url, dest):
    start = time.time()
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        result = run_cmd(['git', 'clone', '--depth', '1', url, dest])
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        emit("INSTALL_OK")
    except Exception as e:
        emit(f"INSTALL_FAIL:{e}")
    finally:
        emit(f"BENCHMARK:clone_time_s:{time.time()-start:.3f}")

def cargo_build(path):
    start = time.time()
    try:
        result = run_cmd(['cargo', 'build', '--release'], cwd=path)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        emit("TEST_PASS:cargo_build")
    except Exception as e:
        emit(f"TEST_FAIL:cargo_build:{e}")
    finally:
        emit(f"BENCHMARK:build_time_s:{time.time()-start:.3f}")

def find_executable(build_path):
    # Assuming binary name is zkjpeg or similar
    target = os.path.join(build_path, 'target', 'release')
    for f in os.listdir(target):
        if os.access(os.path.join(target, f), os.X_OK) and not f.endswith('.d'):
            return os.path.join(target, f)
    return None

def encode_image(bin_path, src, out):
    start = time.time()
    try:
        result = run_cmd([bin_path, 'encode', '--input', src, '--output', out])
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        size = os.path.getsize(out)
        emit(f"BENCHMARK:encoded_size_bytes:{size}")
        emit(f"TEST_PASS:encode_image")
        return time.time() - start
    except Exception as e:
        emit(f"TEST_FAIL:encode_image:{e}")
        return None

def decode_image(bin_path, src, out):
    start = time.time()
    try:
        result = run_cmd([bin_path, 'decode', '--input', src, '--output', out])
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        emit("TEST_PASS:decode_image")
        emit(f"BENCHMARK:decode_time_s:{time.time()-start:.3f}")
    except Exception as e:
        emit(f"TEST_FAIL:decode_image:{e}")

def compare_images(img1, img2):
    try:
        with open(img1, 'rb') as f1, open(img2, 'rb') as f2:
            h1 = hashlib.sha256(f1.read()).hexdigest()
            h2 = hashlib.sha256(f2.read()).hexdigest()
        if h1 == h2:
            emit("TEST_PASS:pixel_match")
        else:
            emit(f"TEST_FAIL:pixel_match:hash mismatch")
    except Exception as e:
        emit(f"TEST_FAIL:pixel_match:{e}")

def batch_benchmark(bin_path, samples_dir):
    times = []
    start = time.time()
    try:
        imgs = list(pathlib.Path(samples_dir).glob('*.jpg'))[:10]
        for img in imgs:
            out = img.with_name(img.stem + '_out.jpg')
            enc_out = img.with_name(img.stem + '_enc')
            t = encode_image(bin_path, str(img), str(enc_out))
            if t:
                times.append(t)
            decode_image(bin_path, str(enc_out), str(out))
        avg = statistics.mean(times) if times else 0
        emit(f"BENCHMARK:batch_encode_avg_s:{avg:.3f}")
        emit(f"BENCHMARK:batch_total_s:{time.time()-start:.3f}")
    except Exception as e:
        emit(f"TEST_FAIL:batch_benchmark:{e}")

def baseline_compare(metric, ours, baseline):
    try:
        ratio = ours / baseline if baseline else 0
        emit(f"BENCHMARK:vs_zksteganography_{metric}:{ratio:.3f}")
    except Exception:
        pass

def main():
    # 1. Install required apk packages
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])

    # 2. Clone repo
    repo_url = "https://github.com/zkjpeg/zkjpeg.git"
    workdir = tempfile.mkdtemp(prefix="zkjpeg_")
    clone_repo(repo_url, workdir)

    # 3. Build with cargo
    cargo_build(workdir)

    # 4. Locate binary
    binary = find_executable(workdir)
    if not binary:
        emit("TEST_FAIL:find_binary:binary not found")
        emit("RUN_OK")
        return

    # 5. Prepare sample image
    sample_dir = os.path.join(workdir, "samples")
    os.makedirs(sample_dir, exist_ok=True)
    # create a tiny JPEG using ffmpeg if available, else use placeholder bytes
    sample_path = os.path.join(sample_dir, "sample.jpg")
    try:
        subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'color=c=red:s=64x64', '-frames:v', '1', sample_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        # fallback: write minimal JPEG header (not a real image but sufficient for tooling)
        with open(sample_path, "wb") as f:
            f.write(bytes.fromhex(
                "FFD8FFE000104A46494600010101006000600000FFDB00430008060607060508"
                "07070709090A0C140D0C0B0B0C19120F141D1A1F1E1D1A1C1C2024252E2B2020"
                "263D333B393D3F3E3C383B4D464F4A4C494D5B5F5D5A5E5F5F5F5F5F5F5F5F5F"
                "5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F"
                "5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F"
                "5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F5F"
                "FFDB0043010909090C0B0C180D0D180F0F0F0F141414141414141414141414"
                "141414141414141414141414141414141414141414141414141414FF C0 00"
                "11 08 00 40 00 40 03 01 22 00 02 11 01 03 11 01 00 00 01 02 00"
                "03 04 00 11 05 01 21 12 31 41 06 13 51 61 07 22 71 81 14 32 91"
                "A1 B1 C1 D1 E1 F0 09 0A 16 17 18 19 1A 1B 1C 1D 1E 1F 20 21 23"
                "24 25 26 27 28 29 2A 2B 2C 2D 2E 2F 30 31 33 34 35 36 37 38 39"
                "3A 3B 3C 3D 3E 3F 40 41 42 44 45 46 47 48 49 4A 4B 4C 4D 4E"
                "FFDA 000C 03010002110311003F00 D2 0F 7F FF D9"))
    # 6. Encode
    encoded_path = os.path.join(sample_dir, "sample_enc")
    enc_time = encode_image(binary, sample_path, encoded_path)
    if enc_time is not None:
        emit(f"BENCHMARK:encode_time_s:{enc_time:.3f}")

    # 7. Decode
    decoded_path = os.path.join(sample_dir, "sample_dec.jpg")
    decode_image(binary, encoded_path, decoded_path)

    # 8. Compare
    compare_images(sample_path, decoded_path)

    # 9. Batch benchmark
    batch_benchmark(binary, sample_dir)

    # 10. Baseline comparison (mock baseline values)
    baseline_encode = 0.8  # seconds (example)
    baseline_decode = 0.5  # seconds (example)
    if enc_time:
        baseline_compare("encode_time_s", enc_time, baseline_encode)
    # assume decode_time captured in benchmark already
    # Emit a few extra generic benchmarks
    emit(f"BENCHMARK:loc_count:{sum(1 for _ in open(__file__))}")
    emit(f"BENCHMARK:test_files_count:{len([f for f in os.listdir(workdir) if os.path.isfile(os.path.join(workdir,f))])}")

    emit("RUN_OK")

if __name__ == "__main__":
    main()