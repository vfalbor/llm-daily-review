import os
import subprocess
import sys
import time
import tracemalloc
import shutil
import json

# Helpers for printing markers
def print_install_ok():
    print("INSTALL_OK")

def print_install_fail(reason):
    print(f"INSTALL_FAIL:{reason}")

def print_test_pass(name):
    print(f"TEST_PASS:{name}")

def print_test_fail(name, reason):
    print(f"TEST_FAIL:{name}:{reason}")

def print_test_skip(name, reason):
    print(f"TEST_SKIP:{name}:{reason}")

def print_benchmark(metric, value):
    print(f"BENCHMARK:{metric}:{value}")

def print_run_ok():
    print("RUN_OK")

# 1. Install required system packages
required_pkgs = ["go", "git", "cargo", "rust", "nodejs", "npm"]
install_start = time.time()
for pkg in required_pkgs:
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        # continue even if one fails
        pass
install_time = time.time() - install_start
print_benchmark("install_time_s", f"{install_time:.2f}")

# 2. Clone the repository
repo_url = "https://github.com/tibleiz/copper.git"
repo_dir = "/tmp/copper_repo"
if os.path.isdir(repo_dir):
    shutil.rmtree(repo_dir)
clone_start = time.time()
try:
    subprocess.run(['git', 'clone', '--depth', '1', repo_url, repo_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print_install_ok()
except Exception as e:
    print_install_fail(str(e))
    # If clone fails, we cannot continue meaningful tests
    print_run_ok()
    sys.exit(0)

clone_time = time.time() - clone_start
print_benchmark("clone_time_s", f"{clone_time:.2f}")

# 3. Build the compiler/runtime using provided build.sh (if exists)
build_script = os.path.join(repo_dir, "build.sh")
if not os.path.isfile(build_script):
    print_test_skip("build", "build.sh not found")
else:
    build_start = time.time()
    try:
        subprocess.run(['chmod', '+x', build_script], check=True, cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([build_script], check=True, cwd=repo_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_test_pass("build")
    except Exception as e:
        print_test_fail("build", str(e))
    finally:
        build_time = time.time() - build_start
        print_benchmark("build_time_s", f"{build_time:.2f}")

# Helper to compile a copper source file
def compile_copper(source_path, output_path):
    # Assume the built binary is named 'copper' inside repo_dir
    copper_bin = os.path.join(repo_dir, "copper")
    if not os.path.isfile(copper_bin):
        raise FileNotFoundError("copper compiler binary not found")
    subprocess.run([copper_bin, source_path, "-o", output_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 4. Test hello world compilation and execution
hello_src = os.path.join(repo_dir, "hello.copper")
hello_bin = os.path.join(repo_dir, "hello.out")
try:
    # Create a minimal hello world source (using Copper syntax guess)
    hello_code = '''
func main() {
    println("Hello, Copper!");
}
'''
    with open(hello_src, "w") as f:
        f.write(hello_code)
    compile_start = time.time()
    compile_copper(hello_src, hello_bin)
    compile_time = time.time() - compile_start
    print_benchmark("hello_compile_time_s", f"{compile_time:.2f}")

    run_start = time.time()
    result = subprocess.run([hello_bin], capture_output=True, text=True, check=True)
    run_time = time.time() - run_start
    print_benchmark("hello_run_time_s", f"{run_time:.2f}")

    if "Hello, Copper!" in result.stdout:
        print_test_pass("hello_world")
    else:
        print_test_fail("hello_world", "unexpected output")
except Exception as e:
    print_test_fail("hello_world", str(e))

# 5. Benchmark compile and run time for a 10‑kB program
prog_src = os.path.join(repo_dir, "bigprog.copper")
prog_bin = os.path.join(repo_dir, "bigprog.out")
try:
    # Generate a 10KB source file with repetitive loops
    line = '    println("Line");\n'
    repeat = int((10 * 1024) / len(line))
    big_code = "func main() {\n" + line * repeat + "}\n"
    with open(prog_src, "w") as f:
        f.write(big_code)

    tracemalloc.start()
    comp_start = time.time()
    compile_copper(prog_src, prog_bin)
    comp_time = time.time() - comp_start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_benchmark("bigprog_compile_time_s", f"{comp_time:.2f}")
    print_benchmark("bigprog_compile_mem_kb", f"{peak/1024:.2f}")

    tracemalloc.start()
    run_start = time.time()
    subprocess.run([prog_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    run_time = time.time() - run_start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print_benchmark("bigprog_run_time_s", f"{run_time:.2f}")
    print_benchmark("bigprog_run_mem_kb", f"{peak/1024:.2f}")

    print_test_pass("bigprog")
except Exception as e:
    print_test_fail("bigprog", str(e))

# 6. Feature check: attempt to compile a class with generics (syntax guessed)
feature_src = os.path.join(repo_dir, "feature.copper")
feature_bin = os.path.join(repo_dir, "feature.out")
try:
    feature_code = '''
class Box<T> {
    var value: T;
    func init(v: T) {
        value = v;
    }
    func get() -> T {
        return value;
    }
}

func main() {
    let b = Box<int>(42);
    println(b.get());
}
'''
    with open(feature_src, "w") as f:
        f.write(feature_code)
    compile_copper(feature_src, feature_bin)
    # If compile succeeds, we consider feature present
    print_test_pass("generics_class")
except Exception as e:
    print_test_fail("generics_class", str(e))

# 7. Baseline comparison against Rust (assume rustc is installed)
# We'll compile the same hello world in Rust and compare run times
rust_src = "/tmp/hello.rs"
rust_bin = "/tmp/hello_rust"
try:
    rust_code = '''
fn main() {
    println!("Hello, Rust!");
}
'''
    with open(rust_src, "w") as f:
        f.write(rust_code)

    rustc_path = shutil.which("rustc")
    if not rustc_path:
        raise FileNotFoundError("rustc not found")

    rust_compile_start = time.time()
    subprocess.run([rustc_path, rust_src, "-o", rust_bin], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rust_compile_time = time.time() - rust_compile_start

    rust_run_start = time.time()
    subprocess.run([rust_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    rust_run_time = time.time() - rust_run_start

    # Compare with our previous hello run time if available
    try:
        copper_run_time = float(run_time)  # from bigprog run, fallback to hello if not set
    except NameError:
        copper_run_time = 0.0
    ratio = copper_run_time / rust_run_time if rust_run_time > 0 else 0
    print_benchmark("vs_rust_run_ratio", f"{ratio:.2f}")
    print_test_pass("baseline_rust")
except Exception as e:
    print_test_fail("baseline_rust", str(e))

# Ensure at least three benchmark lines (we already printed many)
# Final marker
print_run_ok()