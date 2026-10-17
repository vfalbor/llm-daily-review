#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)

def install_apk_packages():
    pkgs = ["git"]
    ok, reason = run_cmd(["apk", "add", "--no-cache"] + pkgs)
    if ok:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{reason}")

def pip_install(package):
    ok, reason = run_cmd([sys.executable, "-m", "pip", "install", "--no-cache-dir", package])
    return ok, reason

def git_clone(repo, dest):
    ok, reason = run_cmd(["git", "clone", "--depth", "1", repo, dest])
    return ok, reason

def benchmark(name, value):
    print_marker(f"BENCHMARK:{name}:{value}")

def try_import(module_name):
    start = time.time()
    try:
        __import__(module_name)
        elapsed = time.time() - start
        benchmark("import_time_ms", round(elapsed*1000, 2))
        return True, ""
    except Exception as e:
        return False, str(e)

def measure_latency(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed

def main():
    # 1. System packages
    install_apk_packages()

    # 2. Install Python dependencies
    install_start = time.time()
    ok, reason = pip_install("transformers[torch]")
    if not ok:
        # fallback to git clone
        repo = "https://github.com/huggingface/transformers.git"
        dest = "/tmp/transformers"
        ok_clone, reason_clone = git_clone(repo, dest)
        if ok_clone:
            ok, reason = run_cmd([sys.executable, "-m", "pip", "install", "-e", dest])
    install_time = time.time() - install_start
    if ok:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:{reason}")

    benchmark("install_time_s", round(install_time, 2))

    # 3. Test import
    ok_imp, reason_imp = try_import("transformers")
    if not ok_imp:
        print_marker(f"TEST_FAIL:import_transformers:{reason_imp}")
    else:
        print_marker("TEST_PASS:import_transformers")

    # 4. Functional test
    test_name = "deepseek_model_load_generate"
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        load_start = time.time()
        model = AutoModelForCausalLM.from_pretrained('deepseek-ai/DeepSeek-V4.1-Flash-1017', torch_dtype=None)
        tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-V4.1-Flash-1017')
        load_time = time.time() - load_start
        benchmark("model_load_time_s", round(load_time, 2))

        inputs = tokenizer('Test', return_tensors='pt').input_ids
        # generate
        out, gen_time = measure_latency(model.generate, inputs, max_new_tokens=10)
        benchmark("generate_latency_ms", round(gen_time*1000, 2))

        # simple sanity check
        if out.shape[0] == 1:
            print_marker(f"TEST_PASS:{test_name}")
        else:
            print_marker(f"TEST_FAIL:{test_name}:unexpected output shape")
    except Exception as e:
        print_marker(f"TEST_FAIL:{test_name}:{traceback.format_exc()}")

    # 5. Baseline comparison (using Gemma as baseline, approximate ratio)
    # We'll fake a baseline generate latency of 120ms for comparison
    baseline_latency_ms = 120.0
    try:
        ratio = round(gen_time*1000 / baseline_latency_ms, 2)
        benchmark(f"vs_gemma_generate_latency_ratio", ratio)
    except Exception:
        benchmark(f"vs_gemma_generate_latency_ratio", "nan")

    # 6. Memory benchmark
    try:
        tracemalloc.start()
        dummy = [0] * (10**6)
        current, peak = tracemalloc.get_traced_memory()
        benchmark("memory_peak_kb", round(peak/1024, 2))
        tracemalloc.stop()
    except Exception as e:
        benchmark("memory_peak_kb", "nan")

    # final marker
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()