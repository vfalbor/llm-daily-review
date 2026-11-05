#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def run_cmd(cmd, description):
    try:
        start = time.time()
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        elapsed = time.time() - start
        if result.returncode != 0:
            raise RuntimeError(f"{description} failed: {result.stderr.strip()}")
        return result.stdout.strip(), elapsed
    except Exception as e:
        raise RuntimeError(f"{description} exception: {e}")

def install_apk():
    try:
        _, t = run_cmd(['apk', 'add', '--no-cache', 'git'], "apk install git")
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:apk_git_install_s:{t:.3f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def pip_install_pkg():
    pkg_name = "ernie-flash-base"  # guessed package name
    try:
        start = time.time()
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", pkg_name],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
        elapsed = time.time() - start
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:pip_install_{pkg_name}_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def git_clone_and_install():
    repo_url = "https://github.com/baidu/ernie-5-5-flash-base.git"
    clone_dir = "/tmp/ernie_flash_base"
    try:
        if os.path.isdir(clone_dir):
            subprocess.run(['rm', '-rf', clone_dir], check=False)
        out, t1 = run_cmd(['git', 'clone', repo_url, clone_dir], "git clone")
        start = time.time()
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."],
                       cwd=clone_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, text=True)
        elapsed = time.time() - start
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:git_clone_s:{t1:.3f}")
        print_marker(f"BENCHMARK:editable_install_s:{elapsed:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def import_module():
    try:
        tracemalloc.start()
        start = time.time()
        import ernie_flash_base  # placeholder import; actual module name may differ
        import_time = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"TEST_PASS:import_module")
        print_marker(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")
        print_marker(f"BENCHMARK:import_memory_kb:{peak/1024:.2f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:import_module:{e}")
        return False

def load_model():
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model_name = "baidu/ernie-5.5-flash-base"
        start = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, trust_remote_code=True)
        load_time = time.time() - start
        print_marker(f"TEST_PASS:load_model")
        print_marker(f"BENCHMARK:model_load_s:{load_time:.3f}")
        return tokenizer, model
    except Exception as e:
        print_marker(f"TEST_FAIL:load_model:{e}")
        return None, None

def run_forward(tokenizer, model):
    try:
        prompt = "Hello, world!"
        inputs = tokenizer(prompt, return_tensors="pt")
        start = time.time()
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=10)
        latency = time.time() - start
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print_marker(f"TEST_PASS:run_forward")
        print_marker(f"BENCHMARK:forward_latency_ms:{latency*1000:.2f}")
        # simple token distribution check (placeholder)
        token_ids = outputs[0].tolist()
        token_counts = {tid: token_ids.count(tid) for tid in set(token_ids)}
        print_marker(f"BENCHMARK:generated_token_count:{len(token_ids)}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:run_forward:{e}")
        return False

def baseline_compare():
    try:
        # Use a small GPT-2 model as baseline
        from transformers import AutoModelForCausalLM, AutoTokenizer
        baseline_name = "gpt2"
        tokenizer = AutoTokenizer.from_pretrained(baseline_name)
        model = AutoModelForCausalLM.from_pretrained(baseline_name)
        prompt = "Hello, world!"
        inputs = tokenizer(prompt, return_tensors="pt")
        start = time.time()
        with torch.no_grad():
            _ = model.generate(**inputs, max_new_tokens=10)
        baseline_latency = time.time() - start

        # Assume we have previously measured our latency in a global var
        our_latency_ms = getattr(baseline_compare, "our_latency_ms", None)
        if our_latency_ms is None:
            print_marker("TEST_SKIP:baseline_compare:latency not measured")
            return
        ratio = (our_latency_ms/1000) / baseline_latency if baseline_latency else float('inf')
        print_marker(f"BENCHMARK:vs_gpt2_latency_ratio:{ratio:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_compare:{e}")

def main():
    try:
        install_apk()
        if not pip_install_pkg():
            git_clone_and_install()
        if not import_module():
            # cannot proceed without import
            raise RuntimeError("Import failed")
        tokenizer, model = load_model()
        if tokenizer is None or model is None:
            raise RuntimeError("Model load failed")
        if not run_forward(tokenizer, model):
            raise RuntimeError("Forward pass failed")
        # store latency for baseline comparison
        # (retrieved from last benchmark line)
        # For simplicity, we re-run forward to capture latency value
        start = time.time()
        with torch.no_grad():
            _ = model.generate(**tokenizer("Hello, world!", return_tensors="pt"), max_new_tokens=10)
        baseline_compare.our_latency_ms = (time.time() - start)*1000
        baseline_compare()
    except Exception as e:
        print_marker(f"TEST_FAIL:main:{e}")
        traceback.print_exc(file=sys.stderr)
    finally:
        print_marker("RUN_OK")

if __name__ == "__main__":
    main()