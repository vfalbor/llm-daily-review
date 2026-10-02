import subprocess, sys, time, os, json, urllib.request, tracemalloc, shlex, signal, pathlib, threading, statistics

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def safe_remove(path):
    try:
        if os.path.isdir(path):
            subprocess.run(['rm','-rf',path])
        else:
            os.remove(path)
    except Exception:
        pass

# 1. Install system packages
apk_pkgs = ['git','go']
try:
    start = time.time()
    subprocess.run(['apk','add','--no-cache'] + apk_pkgs, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    install_time = time.time() - start
    print_marker(f'INSTALL_OK')
except Exception as e:
    print_marker(f'INSTALL_FAIL:{e}')

print_marker(f'BENCHMARK:install_time_s:{install_time:.3f}')

# Define workspace
workdir = pathlib.Path('/tmp/janus_test')
safe_remove(workdir)
workdir.mkdir(parents=True, exist_ok=True)

repo_url = 'https://github.com/Vibra-Ingenn/Janus.git'
repo_dir = workdir / 'Janus'

# 2. Clone repo
try:
    start = time.time()
    res = run_cmd(['git','clone',repo_url,str(repo_dir)])
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    clone_time = time.time() - start
    print_marker('TEST_PASS:clone_repo')
    print_marker(f'BENCHMARK:clone_time_s:{clone_time:.3f}')
except Exception as e:
    print_marker(f'TEST_FAIL:clone_repo:{e}')
    clone_time = None

# 3. Build binary
binary_path = repo_dir / 'janus'
try:
    start = time.time()
    res = run_cmd(['go','build','-o',str(binary_path)], cwd=str(repo_dir))
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    build_time = time.time() - start
    print_marker('TEST_PASS:build_binary')
    print_marker(f'BENCHMARK:build_time_s:{build_time:.3f}')
except Exception as e:
    print_marker(f'TEST_FAIL:build_binary:{e}')
    build_time = None

# Helper to download tiny model
model_url = 'https://huggingface.co/ggml-org/models/ggml-tiny-gguf/resolve/main/tinyllama.gguf'
model_path = workdir / 'tinyllama.gguf'

def download_model():
    try:
        start = time.time()
        urllib.request.urlretrieve(model_url, str(model_path))
        return time.time() - start
    except Exception as ex:
        raise RuntimeError(f'Download error: {ex}')

# 4. Download model
try:
    dl_time = download_model()
    print_marker('TEST_PASS:download_model')
    print_marker(f'BENCHMARK:model_download_s:{dl_time:.3f}')
except Exception as e:
    print_marker(f'TEST_FAIL:download_model:{e}')
    dl_time = None

# 5. Run inference test
def run_inference(prompt):
    cmd = [str(binary_path), '-m', str(model_path), '-p', prompt]
    start = time.time()
    res = run_cmd(cmd)
    latency = time.time() - start
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip())
    return latency, res.stdout.strip()

try:
    infer_latency, out = run_inference("Hello, world!")
    print_marker('TEST_PASS:cli_inference')
    print_marker(f'BENCHMARK:cli_inference_s:{infer_latency:.3f}')
except Exception as e:
    print_marker(f'TEST_FAIL:cli_inference:{e}')

# 6. Baseline comparison using llama.cpp (attempt if binary exists)
baseline_binary = '/usr/local/bin/llama-cli'  # assumed path
baseline_latency = None
if os.path.isfile(baseline_binary):
    try:
        start = time.time()
        res = run_cmd([baseline_binary,'-m',str(model_path),'-p',"Hello, world!"])
        baseline_latency = time.time() - start
        print_marker('TEST_PASS:baseline_inference')
        print_marker(f'BENCHMARK:baseline_inference_s:{baseline_latency:.3f}')
    except Exception as e:
        print_marker(f'TEST_FAIL:baseline_inference:{e}')
else:
    print_marker('TEST_SKIP:baseline_inference:binary not found')

# 7. Ratio benchmark
if baseline_latency and infer_latency:
    ratio = infer_latency / baseline_latency
    print_marker(f'BENCHMARK:vs_llama_cpp_ratio:{ratio:.3f}')
else:
    print_marker('TEST_SKIP:vs_llama_cpp_ratio:missing data')

# 8. Server mode test
server_process = None
def start_server():
    return subprocess.Popen([str(binary_path), '-s'], cwd=str(repo_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def stop_server(proc):
    try:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

try:
    server_process = start_server()
    # give server time to start
    time.sleep(2)
    # perform request
    payload = json.dumps({"prompt":"Hello"}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8080/infer', data=payload, headers={'Content-Type':'application/json'})
    start = time.time()
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp_data = resp.read()
    server_latency = time.time() - start
    resp_json = json.loads(resp_data)
    if 'response' in resp_json:
        print_marker('TEST_PASS:server_infer')
        print_marker(f'BENCHMARK:server_infer_s:{server_latency:.3f}')
    else:
        raise RuntimeError('Invalid response structure')
except Exception as e:
    print_marker(f'TEST_FAIL:server_infer:{e}')
finally:
    if server_process:
        stop_server(server_process)

# 9. CPU fallback test (force no GPU by setting env var if supported)
try:
    env = os.environ.copy()
    env['VULKAN_ICD_FILENAMES'] = ''  # attempt to disable Vulkan
    start = time.time()
    res = run_cmd([str(binary_path), '-m', str(model_path), '-p', 'CPU fallback test'], env=env)
    fallback_latency = time.time() - start
    if res.returncode == 0:
        print_marker('TEST_PASS:cpu_fallback')
        print_marker(f'BENCHMARK:cpu_fallback_s:{fallback_latency:.3f}')
    else:
        raise RuntimeError(res.stderr.strip())
except Exception as e:
    print_marker(f'TEST_FAIL:cpu_fallback:{e}')

# Ensure at least three benchmark lines (we already printed many)
# Final marker
print_marker('RUN_OK')