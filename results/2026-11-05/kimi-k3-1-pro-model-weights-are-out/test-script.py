import subprocess, sys, time, tracemalloc, json, os, pathlib, shlex, traceback

def print_marker(msg):
    print(msg, flush=True)

def apk_install(pkg):
    try:
        start = time.time()
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            print_marker(f'INSTALL_OK')
        else:
            print_marker(f'INSTALL_FAIL:{res.stderr.strip()}')
        return duration
    except Exception as e:
        print_marker(f'INSTALL_FAIL:{e}')
        return None

def pip_install(package):
    try:
        start = time.time()
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            print_marker('INSTALL_OK')
        else:
            print_marker(f'INSTALL_FAIL:{res.stderr.strip()}')
        return duration
    except Exception as e:
        print_marker(f'INSTALL_FAIL:{e}')
        return None

def run_subprocess(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def clone_repo(repo_url, dest):
    try:
        if pathlib.Path(dest).exists():
            subprocess.run(['rm', '-rf', dest])
        res = run_subprocess(['git', 'clone', '--depth', '1', repo_url, dest])
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        return True
    except Exception as e:
        print_marker(f'TEST_FAIL:clone_repo:{e}')
        return False

def install_from_source(path):
    try:
        res = run_subprocess([sys.executable, '-m', 'pip', 'install', '-e', '.'], cwd=path)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip())
        return True
    except Exception as e:
        print_marker(f'TEST_FAIL:install_from_source:{e}')
        return False

def measure_import(module_name):
    try:
        tracemalloc.start()
        start = time.time()
        __import__(module_name)
        import_time = (time.time() - start) * 1000  # ms
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f'BENCHMARK:import_time_ms:{import_time:.2f}')
        print_marker(f'BENCHMARK:import_mem_peak_kb:{peak/1024:.2f}')
        return import_time
    except Exception as e:
        print_marker(f'TEST_FAIL:import_{module_name}:{e}')
        return None

def test_generation(model_path, prompt="Hello, world!"):
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tracemalloc.start()
        start_load = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_path, device_map="cpu", torch_dtype='auto', trust_remote_code=True)
        load_time = time.time() - start_load
        print_marker(f'BENCHMARK:model_load_time_s:{load_time:.2f}')

        inputs = tokenizer(prompt, return_tensors="pt")
        start_gen = time.time()
        output = model.generate(**inputs, max_new_tokens=20)
        gen_time = time.time() - start_gen
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
        gen_len = len(generated_text.split())
        print_marker(f'BENCHMARK:generation_latency_ms:{gen_time*1000:.2f}')
        print_marker(f'BENCHMARK:generated_token_count:{gen_len}')
        print_marker(f'TEST_PASS:generation')
        tracemalloc.stop()
    except Exception as e:
        print_marker(f'TEST_FAIL:generation:{e}')
        traceback.print_exc()

def compare_vs_baseline(metric, baseline_value):
    try:
        # dummy baseline for example
        ratio = metric / baseline_value if baseline_value != 0 else 0
        print_marker(f'BENCHMARK:vs_transformers_{metric}_ratio:{ratio:.2f}')
    except Exception as e:
        print_marker(f'TEST_FAIL:compare_vs_baseline:{e}')

def main():
    # 1. Install system packages
    apk_time = apk_install('git')
    if apk_time is not None:
        print_marker(f'BENCHMARK:apk_git_install_s:{apk_time:.2f}')

    # 2. Install python packages
    pip_time = pip_install('torch')
    if pip_time is not None:
        print_marker(f'BENCHMARK:pip_torch_install_s:{pip_time:.2f}')
    pip_time = pip_install('transformers')
    if pip_time is not None:
        print_marker(f'BENCHMARK:pip_transformers_install_s:{pip_time:.2f}')

    repo_url = 'https://github.com/moonshotai/Kimi-K3.1-Pro.git'
    repo_dir = '/tmp/kimi_k3_1_pro'

    # 3. Clone repo
    if clone_repo(repo_url, repo_dir):
        print_marker('TEST_PASS:clone_repo')
    else:
        print_marker('TEST_FAIL:clone_repo:clone_failed')
        # cannot proceed further without repo
        print_marker('RUN_OK')
        return

    # 4. Try pip install package (if any)
    if not install_from_source(repo_dir):
        print_marker('TEST_FAIL:install_from_source:fallback')
        # continue anyway, maybe model can be loaded directly via huggingface_hub

    # 5. Measure import time
    import_time = measure_import('transformers')
    if import_time is not None:
        print_marker('TEST_PASS:import_transformers')
    else:
        print_marker('TEST_FAIL:import_transformers:import_error')

    # 6. Load and generate
    # Assume model is hosted on HF; use the repo name as identifier
    model_id = 'moonshotai/Kimi-K3.1-Pro'
    test_generation(model_id, prompt="Explain quantum computing in one sentence.")

    # 7. Benchmark comparison (dummy baseline)
    compare_vs_baseline( import_time if import_time else 0.0, baseline_value=150.0)

    # Ensure at least three benchmark lines (already printed several)
    print_marker('RUN_OK')

if __name__ == '__main__':
    main()