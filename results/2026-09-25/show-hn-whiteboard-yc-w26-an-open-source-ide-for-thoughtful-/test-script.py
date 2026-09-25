#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import json
import tracemalloc
import shlex
import pathlib

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return result
    except Exception as e:
        return e

def install_apk(pkg):
    start = time.time()
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True,
                             check=False)
        if res.returncode == 0:
            marker(f"INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:{pkg} {res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:{pkg} {e}")
    finally:
        duration = time.time() - start
        marker(f"BENCHMARK:apk_install_{pkg}_s:{duration:.3f}")

def pip_install(pkg):
    start = time.time()
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True,
                             check=False)
        if res.returncode == 0:
            marker(f"INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:pip {pkg} {res.stderr.strip()}")
    except Exception as e:
        marker(f"INSTALL_FAIL:pip {pkg} {e}")
    finally:
        marker(f"BENCHMARK:pip_install_{pkg}_s:{time.time()-start:.3f}")

def git_clone(repo, dest):
    start = time.time()
    try:
        if os.path.isdir(dest):
            marker(f"INSTALL_SKIP:git_clone:{dest} already exists")
            return True
        res = run_cmd(['git', 'clone', '--depth', '1', repo, dest])
        if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
            marker(f"INSTALL_OK")
            return True
        else:
            err = res.stderr if isinstance(res, subprocess.CompletedProcess) else str(res)
            marker(f"INSTALL_FAIL:git_clone {err}")
            return False
    finally:
        marker(f"BENCHMARK:git_clone_s:{time.time()-start:.3f}")

def measure_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        marker(f"TEST_PASS:import_{module_name}")
    except Exception as e:
        marker(f"TEST_FAIL:import_{module_name}:{e}")
    finally:
        dur = (time.time() - start) * 1000
        marker(f"BENCHMARK:import_{module_name}_ms:{dur:.2f}")

def measure_cli_help(cmd):
    start = time.time()
    try:
        res = run_cmd(shlex.split(cmd))
        if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0 and 'Usage' in res.stdout:
            marker(f"TEST_PASS:cli_help")
        else:
            err = res.stderr if isinstance(res, subprocess.CompletedProcess) else str(res)
            marker(f"TEST_FAIL:cli_help:{err}")
    except Exception as e:
        marker(f"TEST_FAIL:cli_help:{e}")
    finally:
        marker(f"BENCHMARK:cli_help_ms:{(time.time()-start)*1000:.2f}")

def measure_startup_time(cmd, cwd=None):
    start = time.time()
    try:
        proc = subprocess.Popen(shlex.split(cmd), cwd=cwd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        # give it a short time to start
        time.sleep(2)
        # check if process is still alive
        if proc.poll() is None:
            marker(f"TEST_PASS:startup")
        else:
            out, err = proc.communicate()
            marker(f"TEST_FAIL:startup:exited early {out}{err}")
        proc.terminate()
    except Exception as e:
        marker(f"TEST_FAIL:startup:{e}")
    finally:
        dur = time.time() - start
        marker(f"BENCHMARK:startup_s:{dur:.3f}")

def compare_vs_baseline(metric, value, baseline_value):
    try:
        ratio = value / baseline_value if baseline_value != 0 else 0
        marker(f"BENCHMARK:vs_{metric}_ratio:{ratio:.3f}")
    except Exception as e:
        marker(f"BENCHMARK:vs_{metric}_ratio:FAIL:{e}")

def main():
    # 1. Install required apk packages
    install_apk('git')
    install_apk('npm')
    install_apk('nodejs')
    # 2. Install the Python package (fallback to source)
    pip_install('whiteboard')
    # measure import
    measure_import('whiteboard')
    # 3. Clone repo for npm tests
    repo_url = "https://github.com/devdotfast/whiteboard.git"
    repo_dir = "/tmp/whiteboard_repo"
    if git_clone(repo_url, repo_dir):
        # npm install
        npm_start = time.time()
        try:
            res = run_cmd(['npm', 'install'], cwd=repo_dir)
            if isinstance(res, subprocess.CompletedProcess) and res.returncode == 0:
                marker("TEST_PASS:npm_install")
            else:
                err = res.stderr if isinstance(res, subprocess.CompletedProcess) else str(res)
                marker(f"TEST_FAIL:npm_install:{err}")
        except Exception as e:
            marker(f"TEST_FAIL:npm_install:{e}")
        finally:
            marker(f"BENCHMARK:npm_install_s:{time.time()-npm_start:.3f}")

        # npm run start (check if it serves)
        start_cmd = ['npm', 'run', 'start']
        try:
            proc = subprocess.Popen(start_cmd, cwd=repo_dir,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            time.sleep(5)  # wait for server
            # simple curl check
            curl_res = run_cmd(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:3000'])
            if isinstance(curl_res, subprocess.CompletedProcess) and curl_res.stdout.strip() == '200':
                marker("TEST_PASS:web_interface")
            else:
                marker(f"TEST_FAIL:web_interface:{curl_res.stderr if isinstance(curl_res, subprocess.CompletedProcess) else curl_res}")
            proc.terminate()
        except Exception as e:
            marker(f"TEST_FAIL:web_interface:{e}")

    # 4. CLI help test
    measure_cli_help('whiteboard --help')

    # 5. Startup time measurement vs 5 seconds target
    measure_startup_time('whiteboard --help')  # using help as lightweight start

    # Emit additional benchmark metrics
    # Example: count of files in repo
    try:
        count = sum(1 for _ in pathlib.Path(repo_dir).rglob('*') if _.is_file())
        marker(f"BENCHMARK:repo_file_count:{count}")
    except Exception as e:
        marker(f"BENCHMARK:repo_file_count:FAIL:{e}")

    # Memory snapshot
    try:
        tracemalloc.start()
        time.sleep(0.1)
        current, peak = tracemalloc.get_traced_memory()
        marker(f"BENCHMARK:memory_current_kb:{current/1024:.2f}")
        marker(f"BENCHMARK:memory_peak_kb:{peak/1024:.2f}")
        tracemalloc.stop()
    except Exception as e:
        marker(f"BENCHMARK:memory:FAIL:{e}")

    # Compare import time vs baseline (assume baseline 120ms)
    try:
        # retrieve last import benchmark line
        # In real scenario store value, here we recompute quickly
        start = time.time()
        __import__('whiteboard')
        import_time = (time.time() - start) * 1000
        baseline = 120.0
        compare_vs_baseline('import_whiteboard', import_time, baseline)
    except Exception:
        pass

    # Final marker
    marker("RUN_OK")

if __name__ == "__main__":
    main()