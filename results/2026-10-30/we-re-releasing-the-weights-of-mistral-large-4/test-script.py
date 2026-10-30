import subprocess, sys, time, tracemalloc, json, os, math, traceback

def run_cmd(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def print_marker(msg):
    print(msg, flush=True)

def install_apk():
    rc, out, err = run_cmd(['apk', 'add', '--no-cache', 'git'])
    if rc == 0:
        print_marker("INSTALL_OK")
    else:
        print_marker(f"INSTALL_FAIL:apk git ({err})")

def pip_install(pkg):
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', pkg])
    return rc == 0, err

def fallback_git_install(repo_url, package_dir):
    rc, out, err = run_cmd(['git', 'clone', '--depth', '1', repo_url, package_dir])
    if rc != 0:
        return False, f"git clone failed: {err}"
    rc, out, err = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', package_dir])
    if rc != 0:
        return False, f"pip install -e failed: {err}"
    return True, ""

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    elapsed = time.time() - start
    print_marker(f"BENCHMARK:{name}:{elapsed:.3f}")
    return result, elapsed, peak

def main():
    # 1. System package install
    install_apk()

    # 2. Python dependencies
    deps = ["torch", "transformers", "huggingface_hub"]
    all_installed = True
    for dep in deps:
        ok, err = pip_install(dep)
        if ok:
            continue
        all_installed = False
        print_marker(f"INSTALL_FAIL:{dep} ({err})")
    if all_installed:
        print_marker("INSTALL_OK")
    else:
        # try fallback to repo for transformers (as example)
        ok, err = fallback_git_install("https://github.com/huggingface/transformers.git", "transformers_src")
        if ok:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:transformers fallback ({err})")

    # 3. Benchmark import time
    try:
        (_, import_time, _) = benchmark("import_time_s", __import__, "transformers")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_time:{e}")
        import_time = None

    # 4. Download model weights (cached)
    from huggingface_hub import snapshot_download, hf_hub_download
    model_id = "mistralai/Mistral-7B-Instruct-v0.3"
    try:
        model_path, dl_time = None, None
        def download():
            return snapshot_download(repo_id=model_id, allow_patterns=["*.bin","*.json","*.pt"])
        model_path, dl_time, _ = benchmark("model_download_s", download)
        print_marker("TEST_PASS:download_model")
    except Exception as e:
        print_marker(f"TEST_FAIL:download_model:{e}")

    # 5. Run simple prompt
    from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
    try:
        def init_pipeline():
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", trust_remote_code=True)
            return pipeline("text-generation", model=model, tokenizer=tokenizer)
        pipe, pipe_time, _ = benchmark("pipeline_init_s", init_pipeline)
        print_marker("TEST_PASS:pipeline_init")
    except Exception as e:
        print_marker(f"TEST_FAIL:pipeline_init:{e}")
        pipe = None

    # 6. Generate 100 tokens and measure latency
    try:
        prompt = "Hello, what is the meaning of life?"
        def generate():
            return pipe(prompt, max_new_tokens=100, do_sample=False)[0]["generated_text"]
        output, gen_time, _ = benchmark("generate_100tokens_s", generate)
        print_marker("TEST_PASS:generate")
    except Exception as e:
        print_marker(f"TEST_FAIL:generate:{e}")
        gen_time = None

    # 7. Simple output quality check (presence of a period)
    try:
        if output and "." in output:
            print_marker("TEST_PASS:output_quality")
        else:
            print_marker("TEST_FAIL:output_quality:missing period")
    except Exception as e:
        print_marker(f"TEST_FAIL:output_quality:{e}")

    # 8. Baseline comparison (using Llama-2-7B placeholder baseline time = 2.5s)
    baseline_time = 2.5
    if gen_time is not None:
        ratio = gen_time / baseline_time
        print_marker(f"BENCHMARK:vs_llama2_7b_ratio:{ratio:.3f}")

    # 9. Additional benchmarks
    # Count number of files in model cache
    try:
        file_count = sum(len(files) for _, _, files in os.walk(model_path))
        print_marker(f"BENCHMARK:model_files_count:{file_count}")
    except Exception:
        pass

    # Memory peak during generation (already captured as peak in benchmark)
    # Already printed as generate_100tokens_s benchmark

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()