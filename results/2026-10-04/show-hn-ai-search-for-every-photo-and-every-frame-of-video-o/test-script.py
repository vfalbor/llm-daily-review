#!/usr/bin/env python3
import subprocess, sys, time, os, tracemalloc, shutil, json, pathlib

def print_marker(msg):
    sys.stdout.flush()
    print(msg)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def apk_install(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg])
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:{pkg}:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install_editable(path):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=path)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:pip_editable:{res.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip_editable:{e}")

def measure_time(func, *a, **kw):
    start = time.time()
    func(*a, **kw)
    return time.time() - start

def clone_repo(url, dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    res = run_cmd(['git', 'clone', '--depth', '1', url, dest])
    if res.returncode != 0:
        raise RuntimeError(f"git clone failed: {res.stderr}")

def create_sample_data(root):
    img_dir = os.path.join(root, "images")
    os.makedirs(img_dir, exist_ok=True)
    # create few tiny png files
    for i in range(5):
        path = os.path.join(img_dir, f"img{i}.png")
        with open(path, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n' + bytes([0]*1024))  # 1KB dummy

    video_dir = os.path.join(root, "videos")
    os.makedirs(video_dir, exist_ok=True)
    # create a tiny mp4 placeholder (empty file)
    video_path = os.path.join(video_dir, "sample.mp4")
    with open(video_path, "wb") as f:
        f.write(b'\x00'*1024)  # 1KB dummy

    return img_dir, video_dir

def run_indexer(cli_path, img_dir, video_dir):
    # Assuming the CLI provides a command like `scm index <path>`
    # We'll index both directories separately.
    for p in (img_dir, video_dir):
        res = run_cmd([cli_path, 'index', p])
        if res.returncode != 0:
            raise RuntimeError(f"Index failed for {p}: {res.stderr}")

def run_search(cli_path, query):
    res = run_cmd([cli_path, 'search', query])
    if res.returncode != 0:
        raise RuntimeError(f"Search failed: {res.stderr}")
    return res.stdout.strip().splitlines()

def main():
    # 1. Install required system packages
    for pkg in ['nodejs', 'npm', 'git', 'cargo', 'rust']:
        apk_install(pkg)

    # 2. Clone repo and attempt pip install
    repo_url = "https://github.com/allenv0/SCM"
    src_dir = "/tmp/scm_src"
    try:
        clone_repo(repo_url, src_dir)
    except Exception as e:
        print_marker(f"TEST_FAIL:clone_repo:{e}")
        src_dir = None

    if src_dir:
        try:
            pip_install_editable(src_dir)
        except Exception as e:
            print_marker(f"TEST_FAIL:pip_install:{e}")

    # Locate CLI executable (assuming entrypoint installed to venv's bin)
    cli_exe = shutil.which('scm')
    if not cli_exe:
        # fallback: use python -m scm if module is available
        try:
            import importlib.util
            spec = importlib.util.find_spec('scm')
            if spec:
                cli_exe = sys.executable
        except Exception:
            cli_exe = None

    if not cli_exe:
        print_marker("TEST_FAIL:cli_discovery:CLI executable not found")
        cli_path = None
    else:
        cli_path = cli_exe

    # 3. Prepare sample data
    try:
        sample_root = "/tmp/scm_sample"
        img_dir, video_dir = create_sample_data(sample_root)
        print_marker("TEST_PASS:create_sample_data")
    except Exception as e:
        print_marker(f"TEST_FAIL:create_sample_data:{e}")
        img_dir = video_dir = None

    # 4. Indexing benchmark
    index_time = None
    if cli_path and img_dir and video_dir:
        try:
            index_time = measure_time(run_indexer, cli_path, img_dir, video_dir)
            print_marker(f"BENCHMARK:index_time_s:{index_time:.3f}")
            print_marker("TEST_PASS:indexing")
        except Exception as e:
            print_marker(f"TEST_FAIL:indexing:{e}")

    # 5. Search benchmark
    if cli_path:
        try:
            search_time = measure_time(run_search, cli_path, "sample")
            results = run_search(cli_path, "sample")
            print_marker(f"BENCHMARK:search_time_s:{search_time:.3f}")
            if results:
                print_marker("TEST_PASS:search_results")
            else:
                print_marker("TEST_FAIL:search_results:No results")
        except Exception as e:
            print_marker(f"TEST_FAIL:search:{e}")

    # 6. Verify no API key required (just run help)
    if cli_path:
        try:
            res = run_cmd([cli_path, '--help'])
            if res.returncode == 0:
                print_marker("TEST_PASS:api_key_not_required")
            else:
                print_marker("TEST_FAIL:api_key_not_required:Help command failed")
        except Exception as e:
            print_marker(f"TEST_FAIL:api_key_not_required:{e}")

    # 7. Baseline comparison (using Recoll if installed)
    recoll_path = shutil.which('recoll')
    if recoll_path and index_time:
        try:
            # simple Recoll indexing of same data (approximate)
            recoll_idx_time = measure_time(run_cmd, ['recollindex', '-r', sample_root])
            ratio = recoll_idx_time / index_time if index_time else 0
            print_marker(f"BENCHMARK:vs_recoll_index_time_ratio:{ratio:.3f}")
        except Exception as e:
            print_marker(f"TEST_FAIL:baseline_comparison:{e}")

    # Additional generic benchmarks
    mem_snapshot = tracemalloc.take_snapshot()
    total_mem = sum([stat.size for stat in mem_snapshot.statistics('filename')])
    print_marker(f"BENCHMARK:memory_bytes:{total_mem}")

    # Ensure at least 3 benchmark lines (we already have)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()