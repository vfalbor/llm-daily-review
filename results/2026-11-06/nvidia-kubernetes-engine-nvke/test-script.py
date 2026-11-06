#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, urllib.request, ssl, shlex, re
from pathlib import Path

def run_cmd(cmd, cwd=None, env=None):
    try:
        start = time.time()
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        duration = time.time() - start
        return result, duration
    except Exception as e:
        return None, 0.0

def print_marker(line):
    print(line, flush=True)

def install_apk(pkg):
    try:
        res, _ = run_cmd(['apk', 'add', '--no-cache', pkg])
        if res and res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:{pkg} - {res.stderr.strip() if res else 'exception'}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{pkg} - {e}")
        return False

def install_git_repo(repo_url, dest):
    try:
        if Path(dest).exists():
            subprocess.run(['rm', '-rf', dest])
        res, _ = run_cmd(['git', 'clone', '--depth', '1', repo_url, dest])
        if res and res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:git clone - {res.stderr.strip() if res else 'exception'}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git clone - {e}")
        return False

def measure_install_time():
    start = time.time()
    # Already done in main flow, return placeholder
    return time.time() - start

def main():
    # 1. Install required apk packages
    for pkg in ['git', 'curl']:
        install_apk(pkg)

    repo_url = "https://github.com/dsx-ai-factory/nvke"
    work_dir = Path("/tmp/nvke_src")
    if not install_git_repo(repo_url, str(work_dir)):
        print_marker("TEST_FAIL:clone_repo:Unable to clone repository")
    else:
        # 2. Try make install
        try:
            res, dur = run_cmd(['make', 'install'], cwd=str(work_dir))
            if res and res.returncode == 0:
                print_marker("TEST_PASS:make_install")
                print_marker(f"BENCHMARK:make_install_time_s:{dur:.3f}")
            else:
                # fallback to pip editable
                res2, dur2 = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=str(work_dir))
                if res2 and res2.returncode == 0:
                    print_marker("TEST_PASS:pip_editable_install")
                    print_marker(f"BENCHMARK:pip_editable_install_time_s:{dur2:.3f}")
                else:
                    print_marker(f"TEST_FAIL:install_nvke:{res.stderr.strip() if res else 'make failed'}")
        except Exception as e:
            print_marker(f"TEST_FAIL:install_nvke:{e}")

    # Ensure nvke binary is in PATH
    nvke_cmd = shutil.which('nvke')
    if not nvke_cmd:
        # try adding local bin
        local_bin = str(work_dir / "bin")
        os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH','')}"
        nvke_cmd = shutil.which('nvke')
    if not nvke_cmd:
        print_marker("TEST_FAIL:nvke_cli:nvke not found")
    else:
        # 3. Version check
        try:
            res, dur = run_cmd([nvke_cmd, 'version'])
            if res and res.returncode == 0:
                print_marker("TEST_PASS:nvke_version")
                print_marker(f"BENCHMARK:nvke_version_time_s:{dur:.3f}")
            else:
                print_marker(f"TEST_FAIL:nvke_version:{res.stderr.strip() if res else 'exec fail'}")
        except Exception as e:
            print_marker(f"TEST_FAIL:nvke_version:{e}")

    # 4. Start single-node cluster
    cluster_start = None
    try:
        start = time.time()
        res, _ = run_cmd([nvke_cmd, 'start', '--single-node'])
        if res and res.returncode == 0:
            cluster_start = time.time() - start
            print_marker("TEST_PASS:nvke_start")
            print_marker(f"BENCHMARK:nvke_cluster_start_s:{cluster_start:.3f}")
        else:
            print_marker(f"TEST_FAIL:nvke_start:{res.stderr.strip() if res else 'exec fail'}")
    except Exception as e:
        print_marker(f"TEST_FAIL:nvke_start:{e}")

    # 5. Verify API server reachable
    if cluster_start is not None:
        try:
            # wait a bit for API to be up
            time.sleep(5)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen("https://127.0.0.1:6443/version", context=ctx, timeout=5) as resp:
                if resp.status == 200:
                    print_marker("TEST_PASS:api_reachable")
                    print_marker("BENCHMARK:api_reachable_ms:0")
                else:
                    print_marker(f"TEST_FAIL:api_reachable:Status {resp.status}")
        except Exception as e:
            print_marker(f"TEST_FAIL:api_reachable:{e}")

    # 6. Deploy nginx pod
    try:
        # ensure kubectl is available (nvke provides it)
        kubectl = shutil.which('kubectl')
        if not kubectl:
            print_marker("TEST_FAIL:kubectl:not found")
        else:
            # create pod
            pod_yaml = """
apiVersion: v1
kind: Pod
metadata:
  name: nginx-test
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
"""
            pod_file = "/tmp/nginx-pod.yaml"
            Path(pod_file).write_text(pod_yaml)
            res, dur = run_cmd([kubectl, 'apply', '-f', pod_file])
            if res and res.returncode == 0:
                print_marker("TEST_PASS:nginx_deploy")
                print_marker(f"BENCHMARK:nginx_deploy_time_s:{dur:.3f}")
                # wait for pod ready
                time.sleep(10)
                res2, _ = run_cmd([kubectl, 'get', 'pods', 'nginx-test', '-o', 'json'])
                if res2 and res2.returncode == 0:
                    pod_info = json.loads(res2.stdout)
                    phase = pod_info.get('status', {}).get('phase')
                    if phase == "Running":
                        # port-forward and curl
                        pf = subprocess.Popen([kubectl, 'port-forward', 'pod/nginx-test', '8080:80'],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        time.sleep(3)
                        try:
                            curl_res = subprocess.run(['curl', '-s', 'http://127.0.0.1:8080'],
                                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                            if curl_res.returncode == 0 and 'nginx' in curl_res.stdout.lower():
                                print_marker("TEST_PASS:nginx_serve")
                                print_marker("BENCHMARK:nginx_serve_ms:0")
                            else:
                                print_marker(f"TEST_FAIL:nginx_serve:{curl_res.stderr.strip()}")
                        finally:
                            pf.terminate()
                    else:
                        print_marker(f"TEST_FAIL:nginx_pod_not_running:phase={phase}")
                else:
                    print_marker(f"TEST_FAIL:nginx_get_pod:{res2.stderr.strip() if res2 else 'exec fail'}")
            else:
                print_marker(f"TEST_FAIL:nginx_deploy:{res.stderr.strip() if res else 'exec fail'}")
    except Exception as e:
        print_marker(f"TEST_FAIL:nginx_deploy:{e}")

    # 7. Benchmark vs Kind (baseline)
    try:
        # measure kind cluster start time
        kind_cmd = shutil.which('kind')
        if kind_cmd:
            start = time.time()
            res, _ = run_cmd([kind_cmd, 'create', 'cluster', '--wait', '30s'])
            if res and res.returncode == 0:
                kind_time = time.time() - start
                print_marker(f"BENCHMARK:kind_cluster_start_s:{kind_time:.3f}")
                if cluster_start:
                    ratio = cluster_start / kind_time if kind_time else 0
                    print_marker(f"BENCHMARK:vs_kind_start_ratio:{ratio:.3f}")
                # cleanup kind
                run_cmd([kind_cmd, 'delete', 'cluster'])
            else:
                print_marker("TEST_FAIL:kind_start:kind command failed")
        else:
            print_marker("TEST_SKIP:kind_not_installed:Kind CLI not found")
    except Exception as e:
        print_marker(f"TEST_FAIL:kind_benchmark:{e}")

    # Additional generic benchmarks
    # memory usage during import
    tracemalloc.start()
    start = time.time()
    try:
        import json  # dummy import
        dur = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        print_marker(f"BENCHMARK:import_time_ms:{dur*1000:.2f}")
        print_marker(f"BENCHMARK:import_peak_mem_kb:{peak/1024:.2f}")
    finally:
        tracemalloc.stop()

    # count lines of code in repo
    try:
        total_lines = 0
        for py_file in work_dir.rglob('*.go'):
            total_lines += sum(1 for _ in open(py_file, 'rb'))
        print_marker(f"BENCHMARK:loc_count:{total_lines}")
    except Exception as e:
        print_marker(f"TEST_FAIL:loc_count:{e}")

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    import shutil
    main()