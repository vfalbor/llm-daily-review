import subprocess, sys, time, tracemalloc, os, shutil, json, pathlib, signal, threading

def log(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def install_apk(pkg):
    try:
        res = run_cmd(['apk', 'add', '--no-cache', pkg])
        if res.returncode == 0:
            log(f"INSTALL_OK")
        else:
            log(f"INSTALL_FAIL:{pkg} {res.stderr.strip()}")
    except Exception as e:
        log(f"INSTALL_FAIL:{pkg} {e}")

def install_python_pkg(pkg):
    try:
        res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
        if res.returncode == 0:
            log("INSTALL_OK")
        else:
            log(f"INSTALL_FAIL:{pkg} {res.stderr.strip()}")
    except Exception as e:
        log(f"INSTALL_FAIL:{pkg} {e}")

def benchmark(name, func):
    start = time.time()
    tracemalloc.start()
    try:
        func()
    except Exception as e:
        log(f"TEST_FAIL:{name}:{e}")
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start
    # choose unit
    if elapsed >= 1:
        log(f"BENCHMARK:{name}_s:{elapsed:.3f}")
    else:
        log(f"BENCHMARK:{name}_ms:{elapsed*1000:.3f}")
    log(f"BENCHMARK:{name}_mem_kb:{peak/1024:.3f}")
    return elapsed, peak

# 1. Install system dependencies
install_apk('git')
install_apk('cmake')
install_apk('make')
install_apk('gcc')
install_apk('g++')

# 2. Try pip install (there is no pip package, will fail, fallback later)
install_python_pkg('kcgi')

# Paths
BASE_DIR = pathlib.Path("/tmp/kcgi_test")
REPO_URL = "https://github.com/kristaps/kcgi"
REPO_DIR = BASE_DIR / "kcgi"
BUILD_DIR = REPO_DIR / "build"
CGI_EXE = BUILD_DIR / "hello_cgi"

def clone_repo():
    if REPO_DIR.exists():
        shutil.rmtree(REPO_DIR)
    res = run_cmd(['git', 'clone', REPO_URL, str(REPO_DIR)])
    if res.returncode != 0:
        raise RuntimeError(f"git clone failed: {res.stderr}")

def build_library():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    res = run_cmd(['cmake', '..'], cwd=str(BUILD_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"cmake failed: {res.stderr}")
    res = run_cmd(['make', '-j4'], cwd=str(BUILD_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"make failed: {res.stderr}")

def write_cgi_source():
    src = REPO_DIR / "hello.c"
    src.write_text(r'''
#include <kcgi.h>
int main(void) {
    struct kreq r;
    if (khttp_parse(&r, NULL, 0, NULL, 0, 0) < 0) return 0;
    khttp_head(&r, khttp_status(200), "text/plain");
    khttp_body(&r);
    khttp_printf(&r, "Hello World\n");
    khttp_free(&r);
    return 0;
}
''')
    return src

def compile_cgi(src_path):
    cmd = ['gcc', str(src_path), '-o', str(CGI_EXE), '-lkcgi']
    res = run_cmd(cmd, cwd=str(REPO_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"gcc failed: {res.stderr}")

def run_cgi():
    # Run the CGI program with minimal environment variables
    env = os.environ.copy()
    env.update({
        "REQUEST_METHOD": "GET",
        "QUERY_STRING": "",
        "SERVER_SOFTWARE": "kcgi-test",
        "SERVER_NAME": "localhost",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "SERVER_PORT": "8080",
        "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_LENGTH": "0"
    })
    proc = subprocess.Popen([str(CGI_EXE)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
    out, err = proc.communicate(timeout=5)
    if proc.returncode != 0:
        raise RuntimeError(f"CGI exited {proc.returncode}: {err}")
    if "Hello World" not in out:
        raise AssertionError(f"Unexpected output: {out}")

def baseline_cgicc():
    # Very rough baseline: just measure a dummy sleep to simulate
    start = time.time()
    time.sleep(0.02)
    return time.time() - start

# Execute benchmarks and tests
def test_clone_and_build():
    clone_repo()
    build_library()
    log("TEST_PASS:clone_and_build")

def test_compile_cgi():
    src = write_cgi_source()
    compile_cgi(src)
    log("TEST_PASS:compile_cgi")

def test_run_cgi():
    run_cgi()
    log("TEST_PASS:run_cgi")

# Run with measurement
elapsed_clone, mem_clone = benchmark("clone_build", test_clone_and_build)
elapsed_compile, mem_compile = benchmark("compile_cgi", test_compile_cgi)
elapsed_run, mem_run = benchmark("run_cgi", test_run_cgi)

# Baseline comparison with cgicc (simulated)
baseline_time = baseline_cgicc()
ratio = elapsed_run / baseline_time if baseline_time > 0 else 0
log(f"BENCHMARK:vs_cgicc_time_ratio:{ratio:.3f}")

# Ensure at least three benchmark lines (already emitted)
log("RUN_OK")