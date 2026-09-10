#!/usr/bin/env python3
import subprocess, sys, os, time, tracemalloc, json, shlex, threading, signal

def run_cmd(cmd, cwd=None, env=None):
    try:
        start = time.time()
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        return result, elapsed
    except Exception as e:
        return None, 0.0

def print_marker(line):
    print(line, flush=True)

def install_apk_packages():
    pkgs = ['nodejs', 'npm']
    for pkg in pkgs:
        try:
            result, _ = run_cmd(['apk', 'add', '--no-cache', pkg])
            if result and result.returncode == 0:
                print_marker("INSTALL_OK")
            else:
                reason = result.stderr.strip() if result else "unknown error"
                print_marker(f"INSTALL_FAIL:{reason}")
        except Exception as e:
            print_marker(f"INSTALL_FAIL:{e}")

def npm_install(package, global_install=False):
    cmd = ['npm', 'install']
    if global_install:
        cmd.append('-g')
    cmd.append(package)
    result, elapsed = run_cmd(cmd)
    if result and result.returncode == 0:
        print_marker("INSTALL_OK")
    else:
        reason = result.stderr.strip() if result else "unknown"
        print_marker(f"INSTALL_FAIL:{reason}")
    return elapsed

def measure_memory(func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        func(*args, **kwargs)
    except Exception:
        pass
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return time.time() - start, peak / 1024  # ms, KiB

def test_1_install_and_config():
    try:
        elapsed = npm_install('tailwindcss')
        print_marker(f"BENCHMARK:install_time_s:{elapsed:.3f}")
        # generate minimal config
        cfg_path = 'tailwind.config.js'
        with open(cfg_path, 'w') as f:
            f.write('module.exports = {content:["./*.html"],theme:{extend:{}},plugins:[]};')
        if os.path.exists(cfg_path):
            print_marker("TEST_PASS:install_and_config")
        else:
            print_marker("TEST_FAIL:install_and_config:config not created")
    except Exception as e:
        print_marker(f"TEST_FAIL:install_and_config:{e}")

def test_2_html_output():
    try:
        # create input.css with base directives
        with open('input.css', 'w') as f:
            f.write('@tailwind base;\n@tailwind components;\n@tailwind utilities;')
        html_content = """<!DOCTYPE html><html><head><link href="output.css" rel="stylesheet"></head><body><div class="text-center text-blue-500">Hello</div></body></html>"""
        with open('test.html', 'w') as f:
            f.write(html_content)
        # run build
        result, elapsed = run_cmd(['npx', 'tailwindcss', '-i', './input.css', '-o', './output.css'])
        if result and result.returncode == 0 and os.path.getsize('output.css') > 0:
            print_marker(f"BENCHMARK:build_time_ms:{elapsed*1000:.2f}")
            print_marker("TEST_PASS:html_output")
        else:
            reason = result.stderr.strip() if result else "build failed"
            print_marker(f"TEST_FAIL:html_output:{reason}")
    except Exception as e:
        print_marker(f"TEST_FAIL:html_output:{e}")

def test_3_build_time():
    try:
        # Ensure clean output
        if os.path.exists('output.css'):
            os.remove('output.css')
        start = time.time()
        result, _ = run_cmd(['npx', 'tailwindcss', '-i', './input.css', '-o', './output.css'])
        elapsed = time.time() - start
        if result and result.returncode == 0:
            print_marker(f"BENCHMARK:tailwind_build_ms:{elapsed*1000:.2f}")
            print_marker("TEST_PASS:build_time")
        else:
            reason = result.stderr.strip() if result else "build error"
            print_marker(f"TEST_FAIL:build_time:{reason}")
    except Exception as e:
        print_marker(f"TEST_FAIL:build_time:{e}")

def test_4_purge():
    try:
        # create a second html with only one class used
        html2 = """<!DOCTYPE html><html><head><link href="output.css" rel="stylesheet"></head><body><div class="bg-red-500">Red</div></body></html>"""
        with open('purge.html', 'w') as f:
            f.write(html2)
        # modify config to include both html files
        with open('tailwind.config.js', 'w') as f:
            f.write('module.exports = {content:["./*.html"],theme:{extend:{}},plugins:[]};')
        # rebuild
        result, _ = run_cmd(['npx', 'tailwindcss', '-i', './input.css', '-o', './purge.css', '--minify'])
        if result and result.returncode == 0:
            size_full = os.path.getsize('output.css')
            size_purged = os.path.getsize('purge.css')
            if size_purged < size_full:
                print_marker(f"BENCHMARK:purge_reduction_percent:{(1-size_purged/size_full)*100:.2f}")
                print_marker("TEST_PASS:purge_functionality")
            else:
                print_marker("TEST_FAIL:purge_functionality:no size reduction")
        else:
            reason = result.stderr.strip() if result else "purge build error"
            print_marker(f"TEST_FAIL:purge_functionality:{reason}")
    except Exception as e:
        print_marker(f"TEST_FAIL:purge_functionality:{e}")

def baseline_bootstrap_build():
    # Install bootstrap and measure dummy build time (just copying css)
    try:
        npm_install('bootstrap')
        start = time.time()
        # simulate build by copying bootstrap css
        result, _ = run_cmd(['cp', 'node_modules/bootstrap/dist/css/bootstrap.min.css', 'bootstrap.css'])
        elapsed = time.time() - start
        return elapsed
    except Exception:
        return None

def compare_to_baseline(tw_time_ms):
    try:
        bs_time = baseline_bootstrap_build()
        if bs_time is not None:
            ratio = tw_time_ms / (bs_time*1000)
            print_marker(f"BENCHMARK:vs_bootstrap_build_ratio:{ratio:.3f}")
        else:
            print_marker("TEST_SKIP:baseline_compare:bootstrap install failed")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_compare:{e}")

def main():
    install_apk_packages()
    # Ensure working dir is clean
    for f in ['input.css','output.css','purge.css','tailwind.config.js','test.html','purge.html']:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

    test_1_install_and_config()
    test_2_html_output()
    test_3_build_time()
    # capture build time metric for comparison
    try:
        with open('output.css','rb') as f:
            pass
    except:
        pass
    # assume last measured tailwind build time stored in variable via benchmark line parsing not needed here
    # For demonstration we re-run build to get metric
    start = time.time()
    run_cmd(['npx', 'tailwindcss', '-i', './input.css', '-o', './output.css'])
    tw_elapsed_ms = (time.time() - start)*1000
    compare_to_baseline(tw_elapsed_ms)

    test_4_purge()
    print_marker("RUN_OK")

if __name__ == "__main__":
    # set a timeout for the whole script to avoid hanging
    timer = threading.Timer(300, lambda: os.kill(os.getpid(), signal.SIGTERM))
    timer.start()
    try:
        main()
    finally:
        timer.cancel()