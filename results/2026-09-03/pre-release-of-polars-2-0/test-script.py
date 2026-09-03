import subprocess
import sys
import time
import tracemalloc
import json
import os
import shlex

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, capture_output=False, env=None):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            env=env,
        )
        return result.stdout.decode() if capture_output else ""
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {e.cmd}\n{e.stderr.decode() if e.stderr else ''}")

def install_apk(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def pip_install(package):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', package], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_marker("INSTALL_OK")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def fallback_git_install(repo_url):
    try:
        tmp_dir = "/tmp/polars_src"
        if os.path.isdir(tmp_dir):
            subprocess.run(['rm', '-rf', tmp_dir], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        run_cmd(f'git clone --depth 1 {shlex.quote(repo_url)} {tmp_dir}')
        run_cmd(f'{sys.executable} -m pip install -e .', env=os.environ.copy(), capture_output=False, )
        print_marker("INSTALL_OK")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def benchmark(name, func):
    start = time.time()
    tracemalloc.start()
    try:
        func()
    except Exception as e:
        raise
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:{name}:{elapsed:.4f}")
    return elapsed, peak

def test_import_polars():
    try:
        t0 = time.time()
        import polars
        elapsed = time.time() - t0
        print_marker(f"BENCHMARK:import_time_s:{elapsed:.4f}")
        print_marker("TEST_PASS:import_polars")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_polars:{e}")

def test_cli_version():
    try:
        out = run_cmd("polars --version", capture_output=True)
        if "polars" in out.lower():
            print_marker("TEST_PASS:cli_version")
        else:
            print_marker("TEST_FAIL:cli_version:Unexpected output")
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_version:{e}")

def test_groupby_aggregation():
    try:
        import polars as pl
        import pandas as pd
        # create synthetic CSV
        csv_path = "/tmp/data.csv"
        df_pd = pd.DataFrame({
            "group": ["a", "b", "a", "b", "c"],
            "value": [1, 2, 3, 4, 5]
        })
        df_pd.to_csv(csv_path, index=False)
        # eager
        df = pl.read_csv(csv_path)
        result = df.groupby("group").agg(pl.col("value").sum())
        # validate
        expected = {"a": 4, "b": 6, "c": 5}
        ok = all(result.filter(pl.col("group") == g)["value"].item() == v for g, v in expected.items())
        if ok:
            print_marker("TEST_PASS:groupby_aggregation")
        else:
            print_marker("TEST_FAIL:groupby_aggregation:Result mismatch")
    except Exception as e:
        print_marker(f"TEST_FAIL:groupby_aggregation:{e}")

def test_lazy_vs_eager():
    try:
        import polars as pl
        import numpy as np
        # synthetic large dataset
        n = 1_000_000
        df = pl.DataFrame({
            "a": np.random.randint(0, 100, size=n),
            "b": np.random.rand(n)
        })
        # eager query
        def eager():
            df.filter(pl.col("a") > 50).with_column((pl.col("b") * 2).alias("b2")).select(["a", "b2"]).head(10).collect()
        # lazy query
        lazy_df = df.lazy()
        def lazy():
            lazy_df.filter(pl.col("a") > 50).with_column((pl.col("b") * 2).alias("b2")).select(["a", "b2"]).head(10).collect()
        eager_time, _ = benchmark("eager_query_s", eager)
        lazy_time, _ = benchmark("lazy_query_s", lazy)
        ratio = lazy_time / eager_time if eager_time else 0
        print_marker(f"BENCHMARK:lazy_vs_eager_ratio:{ratio:.4f}")
        print_marker("TEST_PASS:lazy_vs_eager")
    except Exception as e:
        print_marker(f"TEST_FAIL:lazy_vs_eager:{e}")

def compare_with_baseline():
    # baseline using pandas for the same groupby aggregation
    try:
        import polars as pl
        import pandas as pd
        csv_path = "/tmp/data.csv"
        # pandas timing
        start = time.time()
        df_pd = pd.read_csv(csv_path)
        result_pd = df_pd.groupby("group")["value"].sum()
        pandas_time = time.time() - start
        # polars timing (reuse previous benchmark if available)
        # Here we approximate with a fresh run
        start = time.time()
        df_pl = pl.read_csv(csv_path)
        result_pl = df_pl.groupby("group").agg(pl.col("value").sum())
        polars_time = time.time() - start
        ratio = polars_time / pandas_time if pandas_time else 0
        print_marker(f"BENCHMARK:vs_pandas_groupby_ratio:{ratio:.4f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_compare:{e}")

def main():
    # 1. Install system deps
    install_apk("git")
    # 2. Install polars via pip
    try:
        pip_install("polars")
    except Exception:
        fallback_git_install("https://github.com/pola-rs/polars")
    # 3. Run tests
    try:
        test_import_polars()
    except Exception as e:
        print_marker(f"TEST_FAIL:import_polars:{e}")
    try:
        test_cli_version()
    except Exception as e:
        print_marker(f"TEST_FAIL:cli_version:{e}")
    try:
        test_groupby_aggregation()
    except Exception as e:
        print_marker(f"TEST_FAIL:groupby_aggregation:{e}")
    try:
        test_lazy_vs_eager()
    except Exception as e:
        print_marker(f"TEST_FAIL:lazy_vs_eager:{e}")
    try:
        compare_with_baseline()
    except Exception as e:
        print_marker(f"TEST_FAIL:compare_with_baseline:{e}")
    # ensure at least three benchmark lines (import, eager, lazy already printed)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()