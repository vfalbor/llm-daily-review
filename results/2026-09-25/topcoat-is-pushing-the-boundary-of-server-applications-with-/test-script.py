import subprocess, sys, os, time, json, signal, threading, http.client, urllib.request, urllib.error, urllib.parse, tracemalloc, shutil, socket

# Helper to print markers
def marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, **kwargs)
        return result
    except Exception as e:
        return None

def install_apk(pkg):
    res = run_cmd(['apk', 'add', '--no-cache', pkg])
    if res and res.returncode == 0:
        marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else str(e))
        marker(f"INSTALL_FAIL:{reason}")
        return False

def pip_install(pkg):
    res = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg])
    if res and res.returncode == 0:
        marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else "unknown")
        marker(f"INSTALL_FAIL:{reason}")
        return False

def cargo_build(path):
    res = run_cmd(['cargo', 'build', '--release'], cwd=path)
    if res and res.returncode == 0:
        marker("INSTALL_OK")
        return True
    else:
        reason = (res.stderr.strip() if res else "unknown")
        marker(f"INSTALL_FAIL:{reason}")
        return False

def kill_process(p):
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    except Exception:
        pass

# 1. Install system packages
install_apk('nodejs')
install_apk('npm')
install_apk('git')
install_apk('rust')
install_apk('cargo')  # cargo often part of rust

# 2. Install Python dependencies
pip_install('requests')
pip_install('psutil')

import requests, psutil

# Benchmarks storage
benchmarks = []

def add_benchmark(name, value):
    benchmarks.append((name, value))
    marker(f"BENCHMARK:{name}:{value}")

# 3. Clone Topcoat repo
repo_url = "https://github.com/oxidecomputer/topcoat.git"
topcoat_dir = "/tmp/topcoat"
if os.path.isdir(topcoat_dir):
    shutil.rmtree(topcoat_dir)
res = run_cmd(['git', 'clone', '--depth', '1', repo_url, topcoat_dir])
if not (res and res.returncode == 0):
    marker(f"TEST_FAIL:clone_topcoat:Git clone failed")
else:
    marker("TEST_PASS:clone_topcoat")

# 4. Build Topcoat CLI (assume Cargo project)
start = time.time()
if os.path.isdir(os.path.join(topcoat_dir, 'cli')):
    build_ok = cargo_build(os.path.join(topcoat_dir, 'cli'))
else:
    build_ok = cargo_build(topcoat_dir)
build_time = time.time() - start
add_benchmark("topcoat_build_time_s", round(build_time, 3))
if not build_ok:
    marker("TEST_FAIL:build_topcoat:Build failed")
else:
    marker("TEST_PASS:build_topcoat")

# Helper to start a binary in background
def start_server(cmd, cwd=None):
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    return proc

# 5. Create hello-world server using Topcoat CLI
hello_dir = "/tmp/topcoat_hello"
if os.path.isdir(hello_dir):
    shutil.rmtree(hello_dir)
os.makedirs(hello_dir, exist_ok=True)

# Write minimal Rust server using Topcoat library (fallback if CLI missing)
main_rs = r'''
use topcoat::prelude::*;
#[tokio::main]
async fn main() {
    let app = App::new().route("/", get(|| async { "Hello, Topcoat!" }));
    serve(app).await;
}
'''
with open(os.path.join(hello_dir, "Cargo.toml"), "w") as f:
    f.write('[package]\nname = "topcoat_hello"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\ntopcoat = { path = "' + topcoat_dir + '" }\n')
with open(os.path.join(hello_dir, "src.rs"), "w") as f:
    f.write(main_rs)

# Build hello server
start = time.time()
res = run_cmd(['cargo', 'run', '--release'], cwd=hello_dir)
hello_build_time = time.time() - start
add_benchmark("topcoat_hello_build_time_s", round(hello_build_time,3))
if res and res.returncode != 0:
    marker(f"TEST_FAIL:build_hello_server:{res.stderr.strip()}")
else:
    marker("TEST_PASS:build_hello_server")

# Run server
server_proc = start_server(['cargo', 'run', '--release'], cwd=hello_dir)
time.sleep(2)  # give it time to start

# 6. Send HTTP GET request and measure latency
def measure_http(url):
    try:
        t0 = time.time()
        r = requests.get(url, timeout=5)
        latency = (time.time() - t0) * 1000  # ms
        return r.status_code, latency
    except Exception as e:
        return None, str(e)

status, latency = measure_http('http://127.0.0.1:8080/')
if status == 200:
    add_benchmark("topcoat_hello_latency_ms", round(latency,2))
    marker("TEST_PASS:http_hello")
else:
    marker(f"TEST_FAIL:http_hello:{latency}")

# 7. Add background task test (simple concurrency)
# We'll spawn a request while server sleeps for 1s inside route
# Update server code on the fly
concurrent_rs = r'''
use topcoat::prelude::*;
use std::time::Duration;
#[tokio::main]
async fn main() {
    let app = App::new().route("/", get(|| async {
        tokio::time::sleep(Duration::from_secs(1)).await;
        "Done"
    }));
    serve(app).await;
}
'''
with open(os.path.join(hello_dir, "src.rs"), "w") as f:
    f.write(concurrent_rs)
# rebuild
kill_process(server_proc)
server_proc = start_server(['cargo', 'run', '--release'], cwd=hello_dir)
time.sleep(2)

def concurrent_test():
    start = time.time()
    try:
        # fire two requests concurrently
        thread1 = threading.Thread(target=lambda: requests.get('http://127.0.0.1:8080/', timeout=5))
        thread2 = threading.Thread(target=lambda: requests.get('http://127.0.0.1:8080/', timeout=5))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        duration = time.time() - start
        return duration
    except Exception as e:
        return None

duration = concurrent_test()
if duration and duration < 2.0:
    add_benchmark("topcoat_concurrency_seconds", round(duration,3))
    marker("TEST_PASS:concurrency")
else:
    marker(f"TEST_FAIL:concurrency:{duration}")

# Cleanup Topcoat server
kill_process(server_proc)

# 8. Benchmark against Actix minimal server
actix_dir = "/tmp/actix_hello"
if os.path.isdir(actix_dir):
    shutil.rmtree(actix_dir)
os.makedirs(actix_dir, exist_ok=True)
with open(os.path.join(actix_dir, "Cargo.toml"), "w") as f:
    f.write('[package]\nname = "actix_hello"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\nactix-web = "4"\n')
with open(os.path.join(actix_dir, "src.rs"), "w") as f:
    f.write(r'''
use actix_web::{get, App, HttpServer, Responder};

#[get("/")]
async fn hello() -> impl Responder { "Hello, Actix!" }

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| App::new().service(hello))
        .bind("127.0.0.1:8081")?
        .run()
        .await
}
''')
# Build actix
start = time.time()
res = run_cmd(['cargo', 'build', '--release'], cwd=actix_dir)
actix_build = time.time() - start
add_benchmark("actix_build_time_s", round(actix_build,3))
if res and res.returncode != 0:
    marker(f"TEST_FAIL:build_actix:{res.stderr.strip()}")
else:
    marker("TEST_PASS:build_actix")

# Run actix server
actix_proc = start_server(['cargo', 'run', '--release'], cwd=actix_dir)
time.sleep(2)

# Measure throughput (simple count over 2 seconds)
def throughput(url, duration=2):
    end = time.time() + duration
    count = 0
    while time.time() < end:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                count += 1
        except Exception:
            pass
    return count

topcoat_count = throughput('http://127.0.0.1:8080/', 2) if server_proc else 0
actix_count = throughput('http://127.0.0.1:8081/', 2)
add_benchmark("topcoat_rps", topcoat_count/2)
add_benchmark("actix_rps", actix_count/2)

if actix_count > 0:
    ratio = round(topcoat_count/actix_count,3)
    add_benchmark("vs_actix_rps_ratio", ratio)

# Cleanup
kill_process(actix_proc)

# Emit any collected benchmark lines (already printed)
marker("RUN_OK")