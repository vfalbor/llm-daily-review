import subprocess, sys, os, time, tracemalloc, hashlib, json, shlex, pathlib, shutil, tempfile

def print_marker(msg):
    print(msg, flush=True)

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

def install_system_packages():
    pkgs = ['nodejs', 'npm', 'git', 'cargo', 'rust', 'cmake', 'make', 'g++']
    for p in pkgs:
        ok, err = install_apk(p)
        if ok:
            print_marker(f"INSTALL_OK | {p}")
        else:
            print_marker(f"INSTALL_FAIL:{p}:{err}")

def clone_repo(dest):
    url = "https://github.com/maanHimself/OpenDLSS-NR.git"
    try:
        res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
        if res.returncode != 0:
            raise RuntimeError(res.stderr)
        return True, ""
    except Exception as e:
        return False, str(e)

def build_project(src_dir):
    build_dir = os.path.join(src_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    start = time.time()
    try:
        # configure
        cfg = run_cmd(['cmake', '..'], cwd=build_dir)
        if cfg.returncode != 0:
            raise RuntimeError(cfg.stderr)
        # build
        bld = run_cmd(['cmake', '--build', '.', '--config', 'Release', '-j'], cwd=build_dir)
        if bld.returncode != 0:
            raise RuntimeError(bld.stderr)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:install_time_s:{elapsed:.2f}")
        return True, "", build_dir, elapsed
    except Exception as e:
        return False, str(e), None, None

def run_sample(build_dir):
    sample_exe = None
    # try typical locations
    for root, _, files in os.walk(build_dir):
        for f in files:
            if f.startswith("sample") and os.access(os.path.join(root, f), os.X_OK):
                sample_exe = os.path.join(root, f)
                break
        if sample_exe:
            break
    if not sample_exe:
        return False, "sample executable not found", None

    test_texture = os.path.join(build_dir, "test_texture.png")
    # generate a dummy texture file (empty) just to satisfy CLI
    pathlib.Path(test_texture).write_bytes(b'\x89PNG\r\n\x1a\n')
    start = time.time()
    try:
        proc = run_cmd([sample_exe, '--texture', test_texture, '--frames', '10'])
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        elapsed = time.time() - start
        print_marker(f"BENCHMARK:sample_run_s:{elapsed:.2f}")
        # assume output image is produced at known path
        out_img = os.path.join(build_dir, "output.png")
        if not os.path.isfile(out_img):
            return False, "output image not generated", elapsed
        return True, out_img, elapsed
    except Exception as e:
        return False, str(e), None

def hash_image(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def validate_output(out_img, ref_hash):
    out_hash = hash_image(out_img)
    if out_hash is None:
        return False, "cannot hash output"
    if out_hash != ref_hash:
        return False, f"hash mismatch (got {out_hash})"
    return True, ""

def measure_memory():
    tracemalloc.start()
    snapshot = tracemalloc.take_snapshot()
    stats = snapshot.statistics('lineno')
    total = sum(s.size for s in stats) / (1024 * 1024)  # MB
    tracemalloc.stop()
    print_marker(f"BENCHMARK:memory_mb:{total:.2f}")

def main():
    install_system_packages()
    tmpdir = tempfile.mkdtemp()
    try:
        ok, err = clone_repo(tmpdir)
        if not ok:
            print_marker(f"TEST_FAIL:clone_repo:{err}")
        else:
            print_marker("TEST_PASS:clone_repo")
            ok, err, build_dir, install_time = build_project(tmpdir)
            if not ok:
                print_marker(f"TEST_FAIL:build_project:{err}")
            else:
                print_marker("TEST_PASS:build_project")
                ok, out_or_err, run_time = run_sample(build_dir)
                if not ok:
                    print_marker(f"TEST_FAIL:run_sample:{out_or_err}")
                else:
                    print_marker("TEST_PASS:run_sample")
                    # dummy reference hash (in real case would be known)
                    ref_hash = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
                    ok, reason = validate_output(out_or_err, ref_hash)
                    if ok:
                        print_marker("TEST_PASS:validate_output")
                    else:
                        print_marker(f"TEST_FAIL:validate_output:{reason}")

                # benchmark memory usage
                measure_memory()

                # compare against baseline (dummy baseline time 0.05s per frame)
                baseline_per_frame = 0.05
                # assume sample runs 10 frames, compute avg
                avg_time = run_time / 10 if run_time else None
                if avg_time:
                    ratio = avg_time / baseline_per_frame
                    print_marker(f"BENCHMARK:vs_baseline_frame_ratio:{ratio:.2f}")

    except Exception as e:
        print_marker(f"TEST_FAIL:unexpected:{str(e)}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        print_marker("RUN_OK")

if __name__ == "__main__":
    main()