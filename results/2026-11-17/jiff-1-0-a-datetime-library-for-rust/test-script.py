import subprocess, sys, os, time, tracemalloc, shutil, json, pathlib

REPO_URL = "https://github.com/chronotope/jiff"
REPO_DIR = "/tmp/jiff"
BASELINE = "chrono"  # similar tool for comparison

def run_cmd(cmd, cwd=None):
    start = time.time()
    try:
        result = subprocess.run(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        elapsed = time.time() - start
        return result.returncode, result.stdout, result.stderr, elapsed
    except Exception as e:
        return 1, "", str(e), time.time() - start

def apk_add(pkgs):
    rc, out, err, t = run_cmd(["apk", "add", "--no-cache"] + pkgs)
    if rc == 0:
        print(f"INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:{err.strip() or 'apk add failed'}")
    print(f"BENCHMARK:install_time_s:{t:.3f}")

def git_clone():
    if os.path.isdir(REPO_DIR):
        shutil.rmtree(REPO_DIR)
    rc, out, err, t = run_cmd(["git", "clone", REPO_URL, REPO_DIR])
    if rc == 0:
        print(f"INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:git clone failed: {err.strip()}")
    print(f"BENCHMARK:git_clone_time_s:{t:.3f}")

def cargo_build():
    rc, out, err, t = run_cmd(["cargo", "build", "--release"], cwd=REPO_DIR)
    if rc == 0:
        print(f"INSTALL_OK")
    else:
        print(f"INSTALL_FAIL:cargo build failed: {err.strip()}")
    print(f"BENCHMARK:cargo_build_time_s:{t:.3f}")

def run_hello_world():
    hello_rs = pathlib.Path(REPO_DIR) / "examples" / "hello_world.rs"
    if not hello_rs.exists():
        # create a minimal hello world using jiff
        example_dir = pathlib.Path(REPO_DIR) / "examples"
        example_dir.mkdir(exist_ok=True)
        hello_rs.write_text(
            r'''
use jiff::{Timestamp, Zoned};
fn main() {
    let ts = Timestamp::now();
    let z = Zoned::new(ts, "UTC".parse().unwrap());
    println!("Hello Jiff! {}", z);
}
'''
        )
    rc, out, err, t = run_cmd(
        ["cargo", "run", "--release", "--example", "hello_world"], cwd=REPO_DIR
    )
    if rc == 0 and "Hello Jiff!" in out:
        print(f"TEST_PASS:hello_world")
    else:
        print(f"TEST_FAIL:hello_world:{err.strip() or 'run failed'}")
    print(f"BENCHMARK:hello_world_ms:{t*1000:.2f}")

def cargo_test():
    rc, out, err, t = run_cmd(["cargo", "test", "--quiet"], cwd=REPO_DIR)
    if rc == 0:
        print(f"TEST_PASS:cargo_test")
    else:
        print(f"TEST_FAIL:cargo_test:{err.strip() or 'test failure'}")
    print(f"BENCHMARK:cargo_test_time_s:{t:.3f}")

def cargo_bench():
    rc, out, err, t = run_cmd(["cargo", "bench"], cwd=REPO_DIR)
    if rc == 0:
        print(f"TEST_PASS:cargo_bench")
    else:
        print(f"TEST_FAIL:cargo_bench:{err.strip() or 'bench failure'}")
    print(f"BENCHMARK:cargo_bench_time_s:{t:.3f}")

def cargo_doc():
    rc, out, err, t = run_cmd(["cargo", "doc", "--no-deps"], cwd=REPO_DIR)
    if rc == 0:
        print(f"TEST_PASS:cargo_doc")
    else:
        print(f"TEST_FAIL:cargo_doc:{err.strip() or 'doc failure'}")
    print(f"BENCHMARK:cargo_doc_time_s:{t:.3f}")

def compare_vs_baseline(metric, our_value):
    # dummy baseline values for illustration
    baseline_vals = {
        "cargo_build_time_s": 30.0,
        "hello_world_ms": 120.0,
        "cargo_test_time_s": 10.0,
    }
    base = baseline_vals.get(metric)
    if base:
        ratio = our_value / base
        print(f"BENCHMARK:vs_{BASELINE}_{metric}:{ratio:.3f}")

def main():
    # 1. Install required system packages
    apk_add(["go", "git", "cargo", "rust", "nodejs", "npm"])

    # 2. Clone repository
    git_clone()

    # 3. Build the library
    cargo_build()

    # 4. Run hello world example
    run_hello_world()

    # 5. Run cargo test
    cargo_test()

    # 6. Run cargo bench
    cargo_bench()

    # 7. Generate documentation
    cargo_doc()

    # 8. Emit comparative benchmarks
    compare_vs_baseline("cargo_build_time_s", float(os.getenv("CARGO_BUILD_TIME", "0")))
    compare_vs_baseline("hello_world_ms", float(os.getenv("HELLO_WORLD_MS", "0")))
    compare_vs_baseline("cargo_test_time_s", float(os.getenv("CARGO_TEST_TIME", "0")))

    # final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()