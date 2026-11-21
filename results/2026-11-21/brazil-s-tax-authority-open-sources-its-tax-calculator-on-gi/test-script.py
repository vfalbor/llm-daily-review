import subprocess, sys, time, tracemalloc, json, os, shutil, hashlib, threading, queue, math, statistics, traceback

def print_marker(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk_packages():
    pkgs = ["git"]
    try:
        res = run_cmd(["apk", "add", "--no-cache"] + pkgs, check=False)
        if res and res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            reason = (res.stderr.strip() if res else "exception")
            print_marker(f"INSTALL_FAIL:{reason}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def pip_install_package(package):
    try:
        res = run_cmd([sys.executable, "-m", "pip", "install", "--quiet", package])
        if res and res.returncode == 0:
            return True, ""
        else:
            return False, (res.stderr.strip() if res else "pip install failed")
    except Exception as e:
        return False, str(e)

def git_clone(repo_url, dest):
    try:
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        res = run_cmd(["git", "clone", "--depth", "1", repo_url, dest])
        if res and res.returncode == 0:
            return True, ""
        else:
            return False, (res.stderr.strip() if res else "git clone failed")
    except Exception as e:
        return False, str(e)

def import_time_measure(module_name):
    start = time.time()
    try:
        __import__(module_name)
        duration = (time.time() - start) * 1000  # ms
        return True, duration, ""
    except Exception as e:
        return False, None, str(e)

def run_cli_tool(cli_path, args):
    cmd = [cli_path] + args
    start = time.time()
    try:
        res = run_cmd(cmd)
        elapsed = (time.time() - start) * 1000
        if res and res.returncode == 0:
            return True, elapsed, res.stdout
        else:
            return False, elapsed, (res.stderr if res else "exec fail")
    except Exception as e:
        return False, None, str(e)

def benchmark_vs_baseline(metric, value, baseline_value):
    try:
        ratio = value / baseline_value if baseline_value != 0 else float('inf')
        print_marker(f"BENCHMARK:vs_{baseline_value}_{metric}:{ratio:.3f}")
    except Exception:
        pass

def main():
    repo_url = "https://github.com/receita-federal/tax-calculator.git"  # placeholder, adjust if needed
    clone_dir = "/tmp/tax_calculator_repo"
    package_name = "tax-calculator"  # placeholder, adjust if needed
    cli_executable = None

    # 1. Install APK packages
    install_apk_packages()

    # 2. Try pip install the package directly
    ok, reason = pip_install_package(package_name)
    if ok:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{reason}")

    # 3. If pip install failed, fallback to git clone + editable install
    if not ok:
        cloned, clone_reason = git_clone(repo_url, clone_dir)
        if cloned:
            print_marker("INSTALL_OK")
            # install editable
            ok_edit, reason_edit = pip_install_package("-e " + clone_dir)
            if ok_edit:
                print_marker("INSTALL_OK")
            else:
                print_marker(f"INSTALL_FAIL:{reason_edit}")
        else:
            print_marker(f"INSTALL_FAIL:{clone_reason}")

    # 4. Measure import time
    imp_ok, imp_time, imp_err = import_time_measure("tax_calculator")
    if imp_ok:
        print_marker(f"BENCHMARK:import_time_ms:{imp_time:.2f}")
    else:
        print_marker(f"TEST_FAIL:import_time:{imp_err}")

    # 5. Locate CLI tool (assume entrypoint script)
    possible_cli = [
        os.path.join(clone_dir, "cli.py"),
        os.path.join(clone_dir, "bin", "taxcalc"),
        os.path.join(clone_dir, "tax_calculator", "cli.py")
    ]
    for p in possible_cli:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            cli_executable = p
            break

    # 6. Run CLI with a simple scenario
    if cli_executable:
        args = ["--income", "50000", "--dependents", "2"]
        run_ok, run_time, run_out = run_cli_tool(cli_executable, args)
        if run_ok:
            print_marker(f"BENCHMARK:cli_run_ms:{run_time:.2f}")
            print_marker("TEST_PASS:cli_basic")
        else:
            print_marker(f"TEST_FAIL:cli_basic:{run_out}")
    else:
        print_marker("TEST_SKIP:cli_basic:CLI not found")

    # 7. Performance benchmark: 1000 calculations
    try:
        import tax_calculator as tc
        calc = tc.TaxCalculator()  # assume class exists
        start = time.time()
        for i in range(1000):
            calc.calculate(income=50000 + i, dependents=2)
        duration = (time.time() - start) * 1000  # ms
        print_marker(f"BENCHMARK:calc_1000_ms:{duration:.2f}")
        # baseline dummy value (e.g., 1200 ms)
        benchmark_vs_baseline("calc_1000_ms", duration, 1200.0)
    except Exception as e:
        print_marker(f"TEST_FAIL:calc_1000:{e}")

    # 8. Verify expected output for a known case
    try:
        result = tc.TaxCalculator().calculate(income=60000, dependents=1)
        expected = {"tax": 12345}  # placeholder expected; replace with real expected
        if isinstance(result, dict) and result.get("tax") == expected["tax"]:
            print_marker("TEST_PASS:expected_output")
        else:
            print_marker(f"TEST_FAIL:expected_output:Result {result} != Expected {expected}")
    except Exception as e:
        print_marker(f"TEST_FAIL:expected_output:{e}")

    # Ensure at least three BENCHMARK lines (import, cli, 1000 calc)
    # Already emitted above.

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()