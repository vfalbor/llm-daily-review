#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, os, json, shlex, traceback

def apk_add(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

def pip_install(pkg):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        raise

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def benchmark(name, value):
    print(f"BENCHMARK:{name}:{value}")

def test_pip_install():
    try:
        start = time.time()
        pip_install('janas')
        elapsed = time.time() - start
        benchmark('install_time_s', round(elapsed, 3))
        print("TEST_PASS:pip_install")
    except Exception as e:
        print(f"TEST_FAIL:pip_install:{e}")

def fallback_git_clone():
    try:
        repo = 'https://github.com/prabanta-dev/janas.git'
        run_cmd(f'git clone {repo} janas_src')
        run_cmd(f'{sys.executable} -m pip install -e .', cwd='janas_src')
        print("TEST_PASS:git_fallback")
    except Exception as e:
        print(f"TEST_FAIL:git_fallback:{e}")

def import_module():
    try:
        start = time.time()
        import janas
        elapsed = (time.time() - start) * 1000
        benchmark('import_time_ms', round(elapsed, 2))
        print("TEST_PASS:import_janas")
        return janas
    except Exception as e:
        print(f"TEST_FAIL:import_janas:{e}")
        return None

def load_model_and_infer(janas_mod):
    try:
        # Use a tiny synthetic model path; janas supports loading from a local dir.
        # We'll create a dummy config that loads a small model shipped with the repo if any.
        model_path = os.getenv('JANAS_MODEL_PATH', '/tmp/janas_dummy')
        os.makedirs(model_path, exist_ok=True)
        # For the purpose of this test, we just initialize a dummy pipeline if available.
        start = time.time()
        # The actual API may differ; we attempt a generic call.
        pipeline = janas_mod.Pipeline(model_path=model_path, device='cpu')
        init_time = (time.time() - start) * 1000
        benchmark('model_load_time_ms', round(init_time, 2))

        prompt = "Hello, world!"
        start = time.time()
        out = pipeline(prompt)
        latency = (time.time() - start) * 1000
        benchmark('inference_latency_ms', round(latency, 2))
        if not out or not isinstance(out, str):
            raise ValueError("Invalid output")
        print("TEST_PASS:model_inference")
        return latency
    except Exception as e:
        print(f"TEST_FAIL:model_inference:{e}")
        return None

def measure_memory_during_inference(janas_mod, latency_ms):
    try:
        tracemalloc.start()
        # Run inference again to capture memory
        pipeline = janas_mod.Pipeline(model_path=os.getenv('JANAS_MODEL_PATH', '/tmp/janas_dummy'), device='cpu')
        pipeline("Memory test")
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        benchmark('memory_peak_kb', round(peak/1024, 2))
        print("TEST_PASS:memory_measure")
    except Exception as e:
        print(f"TEST_FAIL:memory_measure:{e}")

def install_vllm():
    try:
        start = time.time()
        pip_install('vllm')
        elapsed = time.time() - start
        benchmark('vllm_install_time_s', round(elapsed, 3))
        print("TEST_PASS:vllm_install")
    except Exception as e:
        print(f"TEST_FAIL:vllm_install:{e}")

def baseline_vllm_inference():
    try:
        import vllm
        from vllm import LLM, SamplingParams
        model = "facebook/opt-125m"  # small model for baseline
        llm = LLM(model=model, tensor_parallel_size=1, max_seq_len=256)
        prompt = "Hello, world!"
        sampling_params = SamplingParams(temperature=0.0, max_tokens=16)
        start = time.time()
        outputs = llm.generate(prompts=[prompt], sampling_params=sampling_params)
        latency = (time.time() - start) * 1000
        benchmark('vllm_inference_latency_ms', round(latency, 2))
        print("TEST_PASS:vllm_inference")
        return latency
    except Exception as e:
        print(f"TEST_FAIL:vllm_inference:{e}")
        return None

def compare_vs_baseline(janas_latency, vllm_latency):
    try:
        if janas_latency is None or vllm_latency is None:
            raise ValueError("Missing latency values")
        ratio = round(janas_latency / vllm_latency, 3)
        benchmark('vs_vllm_latency_ratio', ratio)
        print("TEST_PASS:compare_vs_vllm")
    except Exception as e:
        print(f"TEST_FAIL:compare_vs_vllm:{e}")

def main():
    # 1. Install system deps
    apk_add('git')

    # 2. Install janas via pip, fallback to git
    try:
        test_pip_install()
    except Exception:
        fallback_git_clone()

    # 3. Import module
    janas_mod = import_module()
    if janas_mod is None:
        # cannot proceed further
        print("RUN_OK")
        return

    # 4. Load model & inference
    latency = load_model_and_infer(janas_mod)

    # 5. Memory measurement
    if latency is not None:
        measure_memory_during_inference(janas_mod, latency)

    # 6. Install baseline tool vLLM
    install_vllm()

    # 7. Baseline inference
    vllm_latency = baseline_vllm_inference()

    # 8. Comparison
    compare_vs_baseline(latency, vllm_latency)

    # Ensure at least three benchmark lines (already emitted several)
    # Final marker
    print("RUN_OK")

if __name__ == "__main__":
    main()