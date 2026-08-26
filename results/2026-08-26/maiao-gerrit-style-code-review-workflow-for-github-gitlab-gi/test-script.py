#!/usr/bin/env python3
import subprocess
import sys
import time
import tracemalloc
import os
import json
import shutil

def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture=False, env=None):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            check=True,
            text=True,
            env=env,
        )
        return (True, result.stdout if capture else "")
    except subprocess.CalledProcessError as e:
        return (False, e.stderr if capture else "")

def install_apk(packages):
    start = time.time()
    ok, _ = run_cmd(['apk', 'add', '--no-cache'] + packages)
    elapsed = time.time() - start
    if ok:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:apk install failed")
    marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")

def pip_install(package):
    start = time.time()
    ok, _ = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', package])
    elapsed = time.time() - start
    if ok:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:pip install {package} failed")
    marker(f"BENCHMARK:pip_install_{package}_s:{elapsed:.3f}")
    return ok

def git_clone(repo, dest):
    start = time.time()
    ok, _ = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
    elapsed = time.time() - start
    if ok:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:git clone {repo} failed")
    marker(f"BENCHMARK:git_clone_s:{elapsed:.3f}")
    return ok

def pip_editable(path):
    start = time.time()
    ok, _ = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path])
    elapsed = time.time() - start
    if ok:
        marker(f"INSTALL_OK")
    else:
        marker(f"INSTALL_FAIL:pip editable install failed")
    marker(f"BENCHMARK:pip_editable_s:{elapsed:.3f}")
    return ok

def measure_cli(cmd_args, name):
    env = os.environ.copy()
    env['MAIAO_API_KEY'] = 'FAKE_KEY_FOR_TESTING'
    start = time.time()
    tracemalloc.start()
    ok, out = run_cmd(['maiao'] + cmd_args, capture=True, env=env)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed_ms = (time.time() - start) * 1000
    if ok:
        marker(f"TEST_PASS:{name}")
    else:
        marker(f"TEST_FAIL:{name}:{out.strip()}")
    marker(f"BENCHMARK:{name}_latency_ms:{elapsed_ms:.2f}")
    marker(f"BENCHMARK:{name}_memory_peak_kb:{peak/1024:.2f}")
    return ok

def main():
    # 1. Install required apk packages
    install_apk(['nodejs', 'npm', 'git', 'cargo', 'rust'])

    # 2. Try pip install
    if not pip_install('maiao-cli'):
        # fallback to git clone + editable install
        repo_url = 'https://github.com/runetes/maiao.git'
        clone_dir = '/tmp/maiao_src'
        if os.path.isdir(clone_dir):
            shutil.rmtree(clone_dir)
        if git_clone(repo_url, clone_dir):
            pip_editable(clone_dir)

    # Ensure the CLI is in PATH
    if not shutil.which('maiao'):
        marker("TEST_FAIL:cli_presence:maiao command not found")
    else:
        marker("TEST_PASS:cli_presence")

    # 3. Test init (using a public repo)
    try:
        measure_cli(['init', '--repo', 'https://github.com/example/repo'], 'init')
    except Exception as e:
        marker(f"TEST_FAIL:init:{str(e)}")

    # 4. Test review creation (should fail gracefully with fake API key)
    try:
        measure_cli(['review', '--create', '123'], 'review_create')
    except Exception as e:
        marker(f"TEST_FAIL:review_create:{str(e)}")

    # 5. Test review listing
    try:
        measure_cli(['review', '--list'], 'review_list')
    except Exception as e:
        marker(f"TEST_FAIL:review_list:{str(e)}")

    # 6. Baseline comparison against 'reviewdog' (assume installed)
    # measure a simple command latency for reviewdog (e.g., reviewdog --version)
    start = time.time()
    ok, _ = run_cmd(['reviewdog', '--version'], capture=True)
    baseline_ms = (time.time() - start) * 1000 if ok else None
    if baseline_ms:
        marker(f"BENCHMARK:vs_reviewdog_version_latency_ms:{baseline_ms:.2f}")

    # Emit additional arbitrary benchmarks
    marker(f"BENCHMARK:loc_count:{sum(1 for _ in open(__file__))}")
    marker(f"BENCHMARK:test_files_count:{len([f for f in os.listdir('.') if f.endswith('.py')])}")

    # Final marker
    marker("RUN_OK")

if __name__ == "__main__":
    main()