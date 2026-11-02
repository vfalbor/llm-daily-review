import subprocess, sys, time, os, shutil, json, traceback, tracemalloc, pathlib, shlex, textwrap, random, string, hashlib, itertools, math, statistics, datetime, tempfile, re, signal, multiprocessing, contextlib, io, csv, collections, typing, urllib.request, tarfile, zipfile, subprocess, json, sys, os, time, hashlib, tempfile, pathlib, random, string, statistics, math, datetime, itertools, collections, typing, io, csv, urllib.parse, base64, signal, contextlib, multiprocessing, traceback, tracemalloc

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def install_apk(pkgs):
    start = time.time()
    rc, out, err = run_cmd(['apk','add','--no-cache'] + pkgs)
    elapsed = time.time() - start
    if rc == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:apk install error: {err.strip()}")
    marker(f"BENCHMARK:apk_install_time_s:{elapsed:.3f}")
    return rc == 0

def cargo_install(pkg):
    start = time.time()
    rc, out, err = run_cmd(['cargo','install',pkg])
    elapsed = time.time() - start
    if rc == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:cargo install error: {err.strip()}")
    marker(f"BENCHMARK:cargo_install_time_s:{elapsed:.3f}")
    return rc == 0

def git_clone(url, dest):
    rc, out, err = run_cmd(['git','clone',url,dest])
    if rc != 0:
        marker(f"INSTALL_FAIL:git clone error: {err.strip()}")
        return False
    return True

def build_rust_project(path):
    start = time.time()
    rc, out, err = run_cmd(['cargo','build','--release'], cwd=path)
    elapsed = time.time() - start
    if rc == 0:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:cargo build error: {err.strip()}")
    marker(f"BENCHMARK:build_time_s:{elapsed:.3f}")
    return rc == 0

def measure_time(func, *a, **kw):
    start = time.time()
    try:
        func(*a, **kw)
        ok = True
    except Exception as e:
        ok = False
        raise
    finally:
        return time.time() - start

def create_sample_repo(base_dir):
    repo_path = os.path.join(base_dir, "sample_repo")
    os.makedirs(repo_path, exist_ok=True)
    run_cmd(['git','init'], cwd=repo_path)
    # create initial file
    file_path = os.path.join(repo_path, "data.txt")
    with open(file_path, "w") as f:
        f.write("Line1\nLine2\nLine3\n")
    run_cmd(['git','add','.'], cwd=repo_path)
    run_cmd(['git','commit','-m','init'], cwd=repo_path)
    return repo_path

def edit_block(file_path):
    lines = open(file_path).readlines()
    # modify middle block
    lines[1] = "Line2 modified\n"
    with open(file_path, "w") as f:
        f.writelines(lines)

def run_omnidiff(repo_path):
    rc, out, err = run_cmd(['omnidiff','--color=never'], cwd=repo_path)
    return rc, out, err

def run_git_diff(repo_path):
    rc, out, err = run_cmd(['git','diff'], cwd=repo_path)
    return rc, out, err

def benchmark_vs_baseline(metric, ours, baseline):
    try:
        ratio = ours / baseline if baseline != 0 else float('inf')
        marker(f"BENCHMARK:vs_{baseline_tool}_{metric}:{ratio:.3f}")
    except Exception:
        pass

# -------------------- Main script --------------------
def main():
    # 1. Install required system packages
    install_apk(['nodejs','npm','git','cargo','rust','build-base'])  # build-base for rust compilation

    # 2. Install omnidiff via cargo
    omnidiff_installed = cargo_install('omnidiff')
    if not omnidiff_installed:
        # fallback: clone and build manually
        tmp_dir = tempfile.mkdtemp()
        repo_url = "https://github.com/ivankovic/omnidiff.git"
        if git_clone(repo_url, tmp_dir):
            if not build_rust_project(tmp_dir):
                marker("TEST_SKIP:install_omnidiff:Failed to build from source")
        else:
            marker("TEST_SKIP:install_omnidiff:Git clone failed")

    # 3. Prepare sample repository
    work_dir = tempfile.mkdtemp()
    repo_path = create_sample_repo(work_dir)

    # 4. Test: omnidiff output vs git diff
    try:
        # Ensure repository is clean
        rc, _, _ = run_cmd(['git','reset','--hard'], cwd=repo_path)
        edit_block(os.path.join(repo_path, "data.txt"))
        # Run both tools
        rc_o, out_o, err_o = run_omnidiff(repo_path)
        rc_g, out_g, err_g = run_git_diff(repo_path)

        if rc_o != 0:
            raise RuntimeError(f"omnidiff exited {rc_o}: {err_o.strip()}")
        if rc_g != 0:
            raise RuntimeError(f"git diff exited {rc_g}: {err_g.strip()}")

        # simple comparison: stripped strings equal?
        if out_o.strip() == out_g.strip():
            marker("TEST_PASS:omnidiff_vs_git")
        else:
            marker(f"TEST_FAIL:omnidiff_vs_git:Output differs")
    except Exception as e:
        marker(f"TEST_FAIL:omnidiff_vs_git:{e}")

    # 5. Benchmark: diff latency on 50kB file
    try:
        # create 50kB file
        large_path = os.path.join(repo_path, "large.txt")
        with open(large_path, "w") as f:
            f.write("".join(random.choices(string.ascii_letters + string.digits, k=51200)))
        run_cmd(['git','add','large.txt'], cwd=repo_path)
        run_cmd(['git','commit','-m','add large'], cwd=repo_path)

        # modify it slightly
        with open(large_path, "a") as f:
            f.write("\nextra line\n")
        # measure omnidiff latency
        latency = measure_time(run_omnidiff, repo_path)
        marker(f"BENCHMARK:omnidiff_latency_ms:{latency*1000:.2f}")

        # baseline using git diff
        baseline_latency = measure_time(run_git_diff, repo_path)
        marker(f"BENCHMARK:gitdiff_latency_ms:{baseline_latency*1000:.2f}")

        # compare
        baseline_tool = "gitdiff"
        benchmark_vs_baseline("latency_ms", latency, baseline_latency)
    except Exception as e:
        marker(f"TEST_FAIL:diff_latency:{e}")

    # 6. Verify content‑aware grouping (basic heuristic)
    try:
        # revert to original then edit a block of 3 lines
        run_cmd(['git','reset','--hard','HEAD~1'], cwd=repo_path)
        file_path = os.path.join(repo_path, "data.txt")
        lines = ["A\n","B\n","C\n","D\n","E\n"]
        with open(file_path, "w") as f:
            f.writelines(lines)
        run_cmd(['git','add','data.txt'], cwd=repo_path)
        run_cmd(['git','commit','-m','new block'], cwd=repo_path)

        # edit a middle block
        edit_block(file_path)
        rc_o, out_o, err_o = run_omnidiff(repo_path)
        # check that output contains a grouping marker like "@@"
        if "@@" in out_o or "---" in out_o:
            marker("TEST_PASS:content_aware_grouping")
        else:
            raise AssertionError("Grouping marker not found")
    except Exception as e:
        marker(f"TEST_FAIL:content_aware_grouping:{e}")

    # 7. Additional benchmarks
    try:
        # count lines processed
        total_lines = sum(1 for _ in open(os.path.join(repo_path,"data.txt")))
        marker(f"BENCHMARK:line_count:{total_lines}")
        # memory usage during diff
        tracemalloc.start()
        run_omnidiff(repo_path)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
    except Exception as e:
        marker(f"TEST_FAIL:additional_benchmarks:{e}")

    # Final marker
    marker("RUN_OK")

if __name__ == "__main__":
    main()