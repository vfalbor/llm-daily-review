#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, shutil, pathlib, shlex

def marker(s):
    print(s, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, env=env,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          text=True)

def install_apk(pkg):
    try:
        start = time.time()
        res = subprocess.run(['apk','add','--no-cache',pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if res.returncode == 0:
            marker(f"INSTALL_OK")
        else:
            marker(f"INSTALL_FAIL:apk {pkg} exit {res.returncode}")
        return elapsed
    except Exception as e:
        marker(f"INSTALL_FAIL:apk {pkg} {e}")
        return None

def pip_install(package):
    try:
        start = time.time()
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', package],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if res.returncode == 0:
            marker("INSTALL_OK")
            return elapsed
        else:
            marker(f"INSTALL_FAIL:pip install {package} exit {res.returncode}")
            return None
    except Exception as e:
        marker(f"INSTALL_FAIL:pip install {package} {e}")
        return None

def pip_editable(path):
    try:
        start = time.time()
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'],
                             cwd=path,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if res.returncode == 0:
            marker("INSTALL_OK")
            return elapsed
        else:
            marker(f"INSTALL_FAIL:editable install exit {res.returncode}")
            return None
    except Exception as e:
        marker(f"INSTALL_FAIL:editable install {e}")
        return None

def measure_import(module_name):
    try:
        tracemalloc.start()
        start = time.time()
        __import__(module_name)
        elapsed = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        marker(f"BENCHMARK:import_time_ms:{elapsed:.2f}")
        marker(f"BENCHMARK:import_peak_mem_kb:{peak/1024:.2f}")
        return elapsed
    except Exception as e:
        marker(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def test_cli_help():
    try:
        res = run_cmd('tscert --help')
        if res.returncode == 0:
            marker("TEST_PASS:cli_help")
        else:
            marker(f"TEST_FAIL:cli_help:exit {res.returncode}")
    except Exception as e:
        marker(f"TEST_FAIL:cli_help:{e}")

def compile_ts():
    try:
        workdir = pathlib.Path('/tmp/ts_test')
        workdir.mkdir(parents=True, exist_ok=True)
        ts_code = "function add(a:number,b:number):number{ return a+b; }\n"
        (workdir/'test.ts').write_text(ts_code)
        start = time.time()
        res = run_cmd('tscert test.ts -out test.js', cwd=str(workdir))
        elapsed = (time.time() - start) * 1000
        marker(f"BENCHMARK:compile_time_ms:{elapsed:.2f}")
        out_path = workdir/'test.js'
        if out_path.exists() and res.returncode == 0:
            marker("TEST_PASS:compile_ts")
        else:
            marker(f"TEST_FAIL:compile_ts:output missing or exit {res.returncode}")
    except Exception as e:
        marker(f"TEST_FAIL:compile_ts:{e}")

def type_error_check():
    try:
        workdir = pathlib.Path('/tmp/ts_error')
        workdir.mkdir(parents=True, exist_ok=True)
        ts_code = "let x: string = 5;\n"
        (workdir/'bad.ts').write_text(ts_code)
        start = time.time()
        res = run_cmd('tscert --noEmit bad.ts', cwd=str(workdir))
        elapsed = (time.time() - start) * 1000
        marker(f"BENCHMARK:typecheck_error_ms:{elapsed:.2f}")
        if res.returncode != 0 and "error" in res.stderr.lower():
            marker("TEST_PASS:type_error_check")
        else:
            marker(f"TEST_FAIL:type_error_check:expected error, got rc {res.returncode}")
    except Exception as e:
        marker(f"TEST_FAIL:type_error_check:{e}")

def benchmark_vs_tsc():
    try:
        # create medium repo of 100 simple functions
        workdir = pathlib.Path('/tmp/ts_medium')
        workdir.mkdir(parents=True, exist_ok=True)
        src = ""
        for i in range(100):
            src += f"function f{i}(a:number):number{{return a+{i};}}\n"
        (workdir/'medium.ts').write_text(src)
        # tsc benchmark (if tsc installed)
        tsc_time = None
        if shutil.which('tsc'):
            start = time.time()
            subprocess.run(['tsc', 'medium.ts'], cwd=str(workdir),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tsc_time = (time.time() - start) * 1000
        # tscert benchmark
        start = time.time()
        subprocess.run(['tscert', '--noEmit', 'medium.ts'], cwd=str(workdir),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tscert_time = (time.time() - start) * 1000
        marker(f"BENCHMARK:tscert_check_ms:{tscert_time:.2f}")
        if tsc_time is not None:
            ratio = tscert_time / tsc_time if tsc_time else float('inf')
            marker(f"BENCHMARK:vs_tsc_check_ratio:{ratio:.2f}")
        else:
            marker("TEST_SKIP:vs_tsc_check:tsc not installed")
    except Exception as e:
        marker(f"TEST_FAIL:vs_tsc_check:{e}")

def main():
    # 1. Install system deps
    install_apk('git')
    # 2. Try pip install
    install_time = pip_install('tscert')
    # 3. If pip fails, fallback to source
    if install_time is None:
        # clone repo
        repo_url = 'https://github.com/cristianoc/TScert.git'
        src_dir = pathlib.Path('/tmp/TScert')
        if src_dir.exists():
            shutil.rmtree(src_dir)
        res = run_cmd(f'git clone {repo_url} {src_dir}')
        if res.returncode != 0:
            marker(f"INSTALL_FAIL:git clone {res.stderr.strip()}")
        else:
            pip_editable(src_dir)
    # 4. Measure import
    measure_import('tscert')
    # 5. Run tests
    test_cli_help()
    compile_ts()
    type_error_check()
    benchmark_vs_tsc()
    # Emit some extra benchmarks
    marker(f"BENCHMARK:loc_count:{sum(1 for _ in pathlib.Path('.').rglob('*.py'))}")
    marker(f"BENCHMARK:test_files_count:{len([f for f in pathlib.Path('/tmp').rglob('*.ts')])}")
    # final marker
    marker("RUN_OK")

if __name__ == '__main__':
    main()