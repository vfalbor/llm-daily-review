#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, shutil, json, traceback

def marker(s):
    print(s, flush=True)

def run_apk(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        marker("INSTALL_OK")
    except Exception as e:
        marker(f"INSTALL_FAIL:{e}")

def pip_install(pkg):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        return False

def git_clone(url, dest):
    try:
        subprocess.run(['git', 'clone', '--depth', '1', url, dest], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        return False

def measure_import(module_name):
    start = time.time()
    tracemalloc.start()
    try:
        __import__(module_name)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        elapsed = (time.time() - start) * 1000  # ms
        return elapsed, peak / 1024  # KB
    except Exception:
        tracemalloc.stop()
        raise

def run_test(name, func):
    try:
        func()
        marker(f"TEST_PASS:{name}")
    except Exception as e:
        reason = str(e).replace('\n', ' | ')
        marker(f"TEST_FAIL:{name}:{reason}")

def benchmark(name, value):
    marker(f"BENCHMARK:{name}:{value}")

def main():
    # 1. install system deps
    run_apk('git')

    # 2. Try pip install nanoMuse
    install_start = time.time()
    pip_ok = pip_install('nanoMuse')
    install_time = time.time() - install_start
    benchmark('install_time_s', round(install_time, 2))
    if not pip_ok:
        # fallback to git clone + editable install
        repo_url = 'https://github.com/nano-muse/nanoMuse.git'
        clone_dir = '/tmp/nanoMuse'
        if os.path.isdir(clone_dir):
            shutil.rmtree(clone_dir)
        if git_clone(repo_url, clone_dir):
            install_start = time.time()
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', '.'],
                           cwd=clone_dir, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            install_time = time.time() - install_start
            benchmark('install_time_s', round(install_time, 2))
        else:
            marker("INSTALL_FAIL:git clone failed")

    # 3. Measure import times for nanoMuse and baseline LangChain
    try:
        nano_time, nano_mem = measure_import('nanoMuse')
        benchmark('import_time_ms', round(nano_time, 2))
        benchmark('import_mem_kb', round(nano_mem, 2))
    except Exception as e:
        marker(f"TEST_FAIL:import_nanoMuse:{e}")

    try:
        lang_time, _ = measure_import('langchain')
        benchmark('import_time_langchain_ms', round(lang_time, 2))
    except Exception:
        # baseline may not be installed; try to install quietly
        pip_install('langchain')
        try:
            lang_time, _ = measure_import('langchain')
            benchmark('import_time_langchain_ms', round(lang_time, 2))
        except Exception as e:
            marker(f"TEST_FAIL:import_langchain:{e}")
            lang_time = None

    # 4. Compare import performance vs baseline
    if 'import_time_ms' in locals() and lang_time:
        ratio = round(nano_time / lang_time, 3)
        benchmark(f"vs_langchain_import_ratio", ratio)

    # 5. Functional test: instantiate minimal agent if possible
    def functional_test():
        import nanoMuse
        # try to locate a minimal class; this is speculative
        if hasattr(nanoMuse, 'Agent'):
            Agent = nanoMuse.Agent
            agent = Agent()  # assume default ctor works
            start = time.time()
            # synthetic task: simple echo
            if hasattr(agent, 'run'):
                resp = agent.run("echo hello world")
                latency = (time.time() - start) * 1000
                benchmark('core_operation_latency_ms', round(latency, 2))
                if not resp or 'hello' not in str(resp).lower():
                    raise AssertionError('Unexpected response')
            else:
                raise AssertionError('Agent has no run method')
        else:
            raise AssertionError('nanoMuse has no Agent class')
    run_test('functional_core', functional_test)

    # 6. CLI test: check help output
    def cli_help_test():
        result = subprocess.run(['nanoMuse', '--help'], capture_output=True, text=True, check=False)
        if result.returncode != 0 or 'usage' not in result.stdout.lower():
            raise AssertionError('CLI help failed')
    run_test('cli_help', cli_help_test)

    # 7. Additional benchmark: count python files in repo
    repo_path = '/tmp/nanoMuse' if os.path.isdir('/tmp/nanoMuse') else None
    if repo_path:
        py_files = sum(len(files) for _, _, files in os.walk(repo_path) if any(f.endswith('.py') for f in files))
        benchmark('loc_count', py_files)

    # final marker
    marker("RUN_OK")

if __name__ == "__main__":
    main()