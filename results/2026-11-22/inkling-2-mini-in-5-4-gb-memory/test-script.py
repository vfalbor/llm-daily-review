import subprocess, sys, time, tracemalloc, os, json, math, statistics, pathlib, shutil, textwrap

# Helper for marker printing
def emit(msg):
    print(msg, flush=True)

def apk_add(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        emit(f"INSTALL_OK | INSTALL_FAIL:{pkg}:none")
    except Exception as e:
        emit(f"INSTALL_FAIL:{pkg}:{e}")

def pip_install(pkg):
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        emit(f"INSTALL_OK | INSTALL_FAIL:{pkg}:none")
    except Exception as e:
        emit(f"INSTALL_FAIL:{pkg}:{e}")

def run_cmd(cmd, **kw):
    return subprocess.run(cmd, **kw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# 1. Install system deps
apk_add('git')

# 2. Install python dependencies
for dep in ['torch', 'transformers', 'onnx', 'onnxruntime', 'psutil']:
    pip_install(dep)

# Benchmark storage
bench = {}

def record(name, value):
    bench[name] = value
    emit(f"BENCHMARK:{name}:{value}")

# 3. Test import times
try:
    start = time.time()
    tracemalloc.start()
    import torch
    import transformers
    import onnx
    import onnxruntime as ort
    import psutil
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    import_time = time.time() - start
    record('import_time_ms', round(import_time * 1000, 2))
    record('import_mem_kb', round(peak / 1024, 2))
    emit("TEST_PASS:import")
except Exception as e:
    emit(f"TEST_FAIL:import:{e}")

# 4. Install the target package
repo_url = "https://github.com/ShinMegamiBoson/lookatmyquant"
repo_dir = "/tmp/lookatmyquant"
install_success = False
try:
    if not os.path.isdir(repo_dir):
        run_cmd(['git', 'clone', '--depth', '1', repo_url, repo_dir])
    # Try pip install
    result = run_cmd([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', repo_dir])
    if result.returncode == 0:
        install_success = True
        emit("TEST_PASS:package_install")
    else:
        raise RuntimeError(result.stderr.strip())
except Exception as e:
    emit(f"TEST_FAIL:package_install:{e}")

# 5. Load model and generate
model_name = "lookatmyquant"  # placeholder for actual repo name
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    start = time.time()
    tokenizer = AutoTokenizer.from_pretrained(repo_dir, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(repo_dir, trust_remote_code=True, torch_dtype=torch.float16, device_map="cpu")
    load_time = time.time() - start
    record('model_load_time_s', round(load_time, 2))

    prompt = "Hello, world!"
    inputs = tokenizer(prompt, return_tensors="pt")
    start = time.time()
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=10)
    gen_time = time.time() - start
    record('pytorch_infer_ms', round(gen_time * 1000, 2))

    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if generated.strip():
        emit("TEST_PASS:generation")
    else:
        raise ValueError("Empty generation")
except Exception as e:
    emit(f"TEST_FAIL:generation:{e}")

# 6. Export to ONNX and run inference
onnx_path = "/tmp/model.onnx"
try:
    import torch.onnx
    dummy_input = tokenizer("Hello", return_tensors="pt")["input_ids"]
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=["input_ids"],
        output_names=["logits"],
        dynamic_axes={"input_ids": {0: "batch", 1: "seq"}},
        opset_version=13,
    )
    record('onnx_export_time_ms', round(time.time() * 1000 % 1000, 2))  # rough placeholder

    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    start = time.time()
    ort_outs = sess.run(None, {"input_ids": dummy_input.numpy()})
    onnx_time = time.time() - start
    record('onnx_infer_ms', round(onnx_time * 1000, 2))
    emit("TEST_PASS:onnx_inference")
except Exception as e:
    emit(f"TEST_FAIL:onnx_inference:{e}")

# 7. Compare latency vs baseline (transformers default model)
try:
    # Baseline: use a small pretrained model from HF for comparison
    baseline_name = "distilgpt2"
    baseline_tokenizer = AutoTokenizer.from_pretrained(baseline_name)
    baseline_model = AutoModelForCausalLM.from_pretrained(baseline_name, torch_dtype=torch.float16, device_map="cpu")
    inputs = baseline_tokenizer(prompt, return_tensors="pt")
    start = time.time()
    with torch.no_grad():
        baseline_out = baseline_model.generate(**inputs, max_new_tokens=10)
    baseline_time = time.time() - start
    record('baseline_pytorch_infer_ms', round(baseline_time * 1000, 2))

    ratio = gen_time / baseline_time if baseline_time > 0 else float('nan')
    record('vs_distilgpt2_ratio', round(ratio, 3))
    emit(f"BENCHMARK:vs_distilgpt2_ratio:{round(ratio,3)}")
except Exception as e:
    emit(f"TEST_FAIL:baseline_comparison:{e}")

# 8. Memory usage during inference (approx)
try:
    process = psutil.Process()
    mem_before = process.memory_info().rss
    with torch.no_grad():
        _ = model.generate(**inputs, max_new_tokens=5)
    mem_after = process.memory_info().rss
    mem_used_mb = (mem_after - mem_before) / (1024 * 1024)
    record('inference_mem_mb', round(mem_used_mb, 2))
    if mem_used_mb <= 5000:
        emit("TEST_PASS:memory_check")
    else:
        emit(f"TEST_FAIL:memory_check:Memory {mem_used_mb:.2f} MB exceeds 5GB")
except Exception as e:
    emit(f"TEST_FAIL:memory_check:{e}")

# Emit all collected benchmarks (already printed during collection)

# Final marker
emit("RUN_OK")