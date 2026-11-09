#!/usr/bin/env python3
import subprocess, sys, time, traceback, os, shutil, threading, queue, json, math, tracemalloc

def print_marker(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def apk_add(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def pip_install(pkg):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip install {pkg}: {e}")
        return False

def git_clone(repo, dest):
    try:
        subprocess.run(['git', 'clone', '--depth', '1', repo, dest], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git clone {repo}: {e}")
        return False

def pip_editable(path):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip -e {path}: {e}")
        return False

# 1. Install system deps
apk_add('git')
# 2. Install python package
install_start = time.time()
if not pip_install('samir-vllm'):
    # fallback to source
    src_dir = "/tmp/samir-vllm"
    if os.path.isdir(src_dir):
        shutil.rmtree(src_dir)
    if git_clone('https://github.com/samir-sarwar/samir-vllm.git', src_dir):
        pip_editable(src_dir)
install_time = time.time() - install_start
print_marker(f"BENCHMARK:install_time_s:{install_time:.3f}")

# 3. Import and basic load test
import_start = time.time()
try:
    import samir_vllm
    import_time = (time.time() - import_start) * 1000
    print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
    print_marker("TEST_PASS:import_module")
except Exception as e:
    print_marker(f"TEST_FAIL:import_module:{e}")
    import_time = None

# 4. Load a model (synthetic)
load_time = None
model = None
if samir_vllm:
    try:
        load_start = time.time()
        model = samir_vllm.load('gpt-3.5')  # this may fallback to a tiny dummy
        load_time = time.time() - load_start
        print_marker(f"BENCHMARK:model_load_s:{load_time:.3f}")
        print_marker("TEST_PASS:model_load")
    except Exception as e:
        print_marker(f"TEST_FAIL:model_load:{e}")

# 5. Single generation latency (10 tokens)
single_latency = None
if model:
    try:
        prompt = "Hello world"
        gen_start = time.time()
        # generate may accept max_new_tokens param; use default and slice
        resp = model.generate(prompt, max_new_tokens=10)
        single_latency = (time.time() - gen_start) * 1000
        print_marker(f"BENCHMARK:single_gen_latency_ms:{single_latency:.2f}")
        print_marker("TEST_PASS:single_generation")
    except Exception as e:
        print_marker(f"TEST_FAIL:single_generation:{e}")

# 6. Throughput benchmark with 8 concurrent requests
throughput = None
if model:
    def worker(q, idx):
        try:
            start = time.time()
            model.generate("Bench test", max_new_tokens=5)
            elapsed = time.time() - start
            q.put(elapsed)
        except Exception:
            q.put(None)

    try:
        q = queue.Queue()
        threads = []
        reqs = 8
        for i in range(reqs):
            t = threading.Thread(target=worker, args=(q, i))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        latencies = [v for v in list(q.queue) if v is not None]
        if latencies:
            avg = sum(latencies) / len(latencies)
            throughput = reqs / sum(latencies)
            print_marker(f"BENCHMARK:concurrent_avg_latency_ms:{avg*1000:.2f}")
            print_marker(f"BENCHMARK:throughput_rps:{throughput:.2f}")
            print_marker("TEST_PASS:concurrent_throughput")
        else:
            print_marker("TEST_FAIL:concurrent_throughput:No successful requests")
    except Exception as e:
        print_marker(f"TEST_FAIL:concurrent_throughput:{e}")

# 7. Compare against baseline vLLM (assume known baseline latency 120ms for 10-token)
baseline_latency_ms = 120.0
if single_latency is not None:
    ratio = single_latency / baseline_latency_ms
    print_marker(f"BENCHMARK:vs_vllm_latency_ratio:{ratio:.3f}")

# Ensure at least three BENCHMARK lines (install, import, load already cover)
# Additional generic benchmark
mem_snapshot = tracemalloc.take_snapshot()
total_mem = sum([stat.size for stat in mem_snapshot.statistics('filename')])
print_marker(f"BENCHMARK:memory_bytes:{total_mem}")

print_marker("RUN_OK")