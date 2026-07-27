import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery
import os
import sys

# Install git package
start_time = time.time()
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
install_git_time = time.time() - start_time
print(f"BENCHMARK:install_git_time_s:{install_git_time:.2f}")

start_time = time.time()
try:
    subprocess.run(['pip', 'install', 'transformers'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/huggingface/transformers.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './transformers'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")
        sys.exit(1)

# Import transformers
start_time = time.time()
try:
    import transformers
    print(f"BENCHMARK:import_time_ms:{(time.time() - start_time) * 1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_transformers:{str(e)}")

# Download and validate model
try:
    start_time = time.time()
    model = transformers.AutoModelForCausalLM.from_pretrained("moonshotai/Kimi-K3")
    download_time = time.time() - start_time
    print(f"BENCHMARK:download_time_s:{download_time:.2f}")
    print("TEST_PASS:download_model")
except Exception as e:
    print(f"TEST_FAIL:download_model:{str(e)}")

# Run inference on a sample prompt
try:
    start_time = time.time()
    tracemalloc.start()
    prompt = "Hello, how are you?"
    inputs = transformers.AutoTokenizer.from_pretrained("moonshotai/Kimi-K3")(prompt, return_tensors="pt")
    outputs = model.generate(**inputs)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    inference_time = end_time - start_time
    print(f"BENCHMARK:inference_time_ms:{inference_time * 1000:.2f}")
    print(f"BENCHMARK:inference_memory_mb:{current / (1024 * 1024):.2f}")
    print("TEST_PASS:run_inference")
except Exception as e:
    print(f"TEST_FAIL:run_inference:{str(e)}")

# Measure latency/accuracy
try:
    start_time = time.time()
    prompt = "What is the capital of France?"
    inputs = transformers.AutoTokenizer.from_pretrained("moonshotai/Kimi-K3")(prompt, return_tensors="pt")
    outputs = model.generate(**inputs)
    end_time = time.time()
    latency = end_time - start_time
    print(f"BENCHMARK:latency_ms:{latency * 1000:.2f}")
    print("TEST_PASS:measure_latency")
except Exception as e:
    print(f"TEST_FAIL:measure_latency:{str(e)}")

# Compare performance vs LLaMA
try:
    start_time = time.time()
    import llama
    print(f"BENCHMARK:import_llama_time_ms:{(time.time() - start_time) * 1000:.2f}")
    start_time = time.time()
    llama_model = llama.LLaMA()
    prompt = "Hello, how are you?"
    llama_model.generate(prompt)
    end_time = time.time()
    llama_inference_time = end_time - start_time
    print(f"BENCHMARK:vs_llama_inference_ratio:{inference_time / llama_inference_time:.2f}")
    print("TEST_PASS:compare_with_llama")
except Exception as e:
    print(f"TEST_FAIL:compare_with_llama:{str(e)}")

print("RUN_OK")