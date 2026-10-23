#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, shlex, statistics

def run_cmd(cmd, capture=False, cwd=None):
    try:
        result = subprocess.run(cmd, shell=False, check=False, stdout=subprocess.PIPE if capture else None,
                                stderr=subprocess.PIPE if capture else None, cwd=cwd, text=True)
        return result
    except Exception as e:
        return e

def apk_install(pkg):
    res = run_cmd(['apk','add','--no-cache',pkg])
    if res.returncode==0:
        print(f"INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:apk {pkg} exit {res.returncode}")

def pip_install(pkg):
    res = run_cmd([sys.executable,'-m','pip','install','--no-cache-dir',pkg])
    if res.returncode==0:
        print(f"INSTALL_OK")
        return True
    else:
        print(f"INSTALL_FAIL:pip {pkg} exit {res.returncode}")
        return False

def git_clone(repo, dest):
    if os.path.isdir(dest):
        return True
    res = run_cmd(['git','clone',repo,dest])
    if isinstance(res, Exception) or res.returncode!=0:
        print(f"INSTALL_FAIL:git clone {repo}")
        return False
    print(f"INSTALL_OK")
    return True

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    elapsed = time.time() - start
    print(f"BENCHMARK:{name}:{elapsed:.4f}")
    return elapsed

def test_import():
    start = time.time()
    try:
        import color_names
        print("TEST_PASS:import")
    except Exception as e:
        print(f"TEST_FAIL:import:{e}")
    finally:
        elapsed = time.time() - start
        print(f"BENCHMARK:import_time_s:{elapsed:.4f}")

def test_cli():
    try:
        result = run_cmd(['color-names','--color','skyblue'], capture=True)
        if result.returncode!=0:
            raise RuntimeError(f"exit {result.returncode}")
        out = result.stdout.strip()
        if "skyblue" in out.lower():
            print("TEST_PASS:cli")
        else:
            raise AssertionError("unexpected output")
    except Exception as e:
        print(f"TEST_FAIL:cli:{e}")

def test_js_module():
    # using node to require the installed js module if present
    js_test = """
    const cn = require('color-names');
    const col = cn.getColor('skyblue');
    console.log(JSON.stringify(col));
    """
    try:
        with open('tmp_test.js','w') as f: f.write(js_test)
        result = run_cmd(['node','tmp_test.js'], capture=True)
        os.remove('tmp_test.js')
        if result.returncode!=0:
            raise RuntimeError(f"node exit {result.returncode}")
        data = json.loads(result.stdout)
        if data.get('rgb') and isinstance(data['rgb'], list):
            print("TEST_PASS:js_module")
        else:
            raise AssertionError("invalid data")
    except Exception as e:
        print(f"TEST_FAIL:js_module:{e}")

def test_lookup_latency():
    try:
        import color_names
        colors = ['skyblue','red','green','blue','yellow','magenta','cyan','black','white','gray']
        queries = [colors[i%len(colors)] for i in range(1000)]
        start = time.time()
        for q in queries:
            _ = color_names.get_color(q)
        elapsed = time.time() - start
        print(f"BENCHMARK:lookup_1000_ms:{elapsed*1000:.2f}")
        print("TEST_PASS:lookup_latency")
    except Exception as e:
        print(f"TEST_FAIL:lookup_latency:{e}")

def install_baseline():
    # baseline: color-name-db
    installed = pip_install('color-name-db')
    if not installed:
        return None
    try:
        import colornamedb
        return colornamedb
    except Exception:
        return None

def compare_baseline(metric_name, our_val, baseline_val):
    try:
        ratio = our_val / baseline_val if baseline_val else 0
        print(f"BENCHMARK:vs_color_name_db_{metric_name}:{ratio:.4f}")
    except Exception:
        pass

def main():
    # 1. System packages
    apk_install('git')
    apk_install('nodejs')
    apk_install('npm')
    # 2. Try pip install
    if not pip_install('color-names'):
        # fallback to git clone + editable install
        if git_clone('https://github.com/filipstokes/color-names.git','color-names'):
            pip_install('-e ./color-names')
    # 3. Baseline install
    baseline_mod = install_baseline()
    # 4. Benchmarks & tests
    try:
        test_import()
    except Exception as e:
        print(f"TEST_FAIL:import:{e}")

    try:
        test_cli()
    except Exception as e:
        print(f"TEST_FAIL:cli:{e}")

    try:
        test_js_module()
    except Exception as e:
        print(f"TEST_FAIL:js_module:{e}")

    try:
        test_lookup_latency()
    except Exception as e:
        print(f"TEST_FAIL:lookup_latency:{e}")

    # Example additional benchmark: count files in repo
    try:
        count = sum(len(files) for _,_,files in os.walk('.'))
        print(f"BENCHMARK:loc_count:{count}")
    except Exception:
        pass

    # Compare import time vs baseline if possible
    if baseline_mod:
        try:
            t0 = time.time()
            import color_names
            t1 = time.time()
            our_import = t1 - t0
            tb0 = time.time()
            _ = baseline_mod.ColorNames()
            tb1 = time.time()
            baseline_import = tb1 - tb0
            compare_baseline('import_time_s', our_import, baseline_import)
        except Exception:
            pass

    print("RUN_OK")

if __name__ == "__main__":
    main()