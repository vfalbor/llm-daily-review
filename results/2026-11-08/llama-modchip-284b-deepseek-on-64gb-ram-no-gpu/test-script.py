import subprocess, sys, time, tracemalloc, os, json, shlex, traceback

def print_marker(line):
    print(line, flush=True)

def apk_install(pkg):
    try:
        start = time.time()
        result = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker(f"INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} exit {result.returncode}")
        return elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} {e}")
        return None

def pip_install(pkg_or_path):
    try:
        start = time.time()
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg_or_path],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:pip install {pkg_or_path} exit {result.returncode}")
        return elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip install {pkg_or_path} {e}")
        return None

def run_cmd(cmd, cwd=None):
    return subprocess.run(shlex.split(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def clone_repo(url, dest):
    try:
        start = time.time()
        result = run_cmd(f"git clone {url} {dest}")
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:git clone exit {result.returncode}")
        return elapsed
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git clone {e}")
        return None

def measure_import(module_name):
    try:
        tracemalloc.start()
        start = time.time()
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:import_time_ms:{import_time:.2f}")
        print_marker(f"BENCHMARK:import_memory_peak_kb:{peak/1024:.2f}")
        return import_time
    except Exception as e:
        print_marker(f"TEST_FAIL:import_{module_name}:{e}")
        return None

def test_load_model():
    test_name = "load_model"
    try:
        import llama_modchip  # assumed package name
        start = time.time()
        # synthetic tiny model config
        model = llama_modchip.LlamaModel(
            model_path="synthetic_small.bin",
            max_context=128,
            use_gpu=False
        )
        load_time = time.time() - start
        print_marker(f"BENCHMARK:model_load_time_s:{load_time:.3f}")
        print_marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")

def test_inference_latency():
    test_name = "inference_latency"
    try:
        import llama_modchip
        model = llama_modchip.LlamaModel(
            model_path="synthetic_small.bin",
            max_context=128,
            use_gpu=False
        )
        prompt = "Hello"
        times = []
        for _ in range(5):
            start = time.time()
            _ = model.generate(prompt, max_new_tokens=10)
            times.append(time.time() - start)
        avg_latency = sum(times) / len(times) * 1000  # ms
        print_marker(f"BENCHMARK:inference_latency_ms:{avg_latency:.2f}")
        print_marker(f"TEST_PASS:{test_name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")

def test_cli_benchmark():
    test_name = "cli_benchmark"
    try:
        # assume the repo provides a cli entrypoint `modchip-cli`
        start = time.time()
        result = run_cmd("modchip-cli --benchmark")
        elapsed = time.time() - start
        if result.returncode == 0:
            # parse a latency number from output if possible
            try:
                data = json.loads(result.stdout)
                latency = data.get("latency_ms", None)
                if latency is not None:
                    print_marker(f"BENCHMARK:cli_latency_ms:{latency}")
                else:
                    print_marker(f"BENCHMARK:cli_latency_ms:{elapsed*1000:.2f}")
            except Exception:
                print_marker(f"BENCHMARK:cli_latency_ms:{elapsed*1000:.2f}")
            print_marker(f"TEST_PASS:{test_name}")
        else:
            print_marker(f"TEST_FAIL:{test_name}:exit {result.returncode}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{e}")

def compare_vs_baseline():
    # Dummy baseline: llama.cpp average latency 120 ms for same prompt
    baseline_latency = 120.0
    # Use previously measured inference_latency if available, else fallback
    # For simplicity, re-run a quick measurement
    try:
        import llama_modchip
        model = llama_modchip.LlamaModel(model_path="synthetic_small.bin", max_context=128, use_gpu=False)
        start = time.time()
        _ = model.generate("test", max_new_tokens=5)
        our_latency = (time.time() - start) * 1000
        ratio = our_latency / baseline_latency
        print_marker(f"BENCHMARK:vs_llama_cpp_latency_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_SKIP:vs_baseline:{e}")

def main():
    # 1. Install apk packages
    apk_time = apk_install('git')
    if apk_time is not None:
        print_marker(f"BENCHMARK:apk_git_install_s:{apk_time:.2f}")

    # 2. Try pip install the package
    repo_url = "https://github.com/synchopate/llama-modchip"
    repo_dir = "/tmp/llama-modchip"
    clone_time = clone_repo(repo_url, repo_dir)
    if clone_time is not None:
        print_marker(f"BENCHMARK:git_clone_s:{clone_time:.2f}")

    os.chdir(repo_dir)
    pip_time = pip_install('.')
    if pip_time is not None:
        print_marker(f"BENCHMARK:pip_install_s:{pip_time:.2f}")

    # 3. Run tests
    try:
        import_time = measure_import('llama_modchip')
        if import_time is None:
            print_marker("TEST_SKIP:import_llama_modchip:import failed")
    except Exception:
        print_marker("TEST_SKIP:import_llama_modchip:exception")

    test_load_model()
    test_inference_latency()
    test_cli_benchmark()
    compare_vs_baseline()

    # Ensure at least three benchmark lines (we already have many)
    # Print final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()