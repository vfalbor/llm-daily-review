import subprocess
import time
import tracemalloc
import importlib.util
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'transformers'], check=True)
except subprocess.CalledProcessError:
    subprocess.run(['git', 'clone', 'https://github.com/huggingface/transformers.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './transformers'], check=True)

# Load the module
try:
    spec = importlib.util.find_spec("transformers")
    if spec is None:
        print("INSTALL_FAIL:transformers")
        sys.exit(1)
except Exception as e:
    print(f"INSTALL_FAIL:transformers:{e}")
    sys.exit(1)

print("INSTALL_OK")

# Import the module and measure import time
start_time = time.time()
try:
    import transformers
    import torch
except Exception as e:
    print(f"TEST_FAIL:import_transformers:{e}")
    sys.exit(1)
import_time = (time.time() - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time:.2f}")

# Run a text input through the model and verify output
try:
    model = transformers.AutoModelForCausalLM.from_pretrained("webml-community/bonsai-webgpu")
    inputs = torch.tensor([[1, 2, 3]])
    output = model.generate(inputs)
    if output is None:
        print("TEST_FAIL:generate_output:None")
    else:
        print("TEST_PASS:generate_output")
except Exception as e:
    print(f"TEST_FAIL:generate_output:{e}")

# Compare inference speed vs full-precision model
try:
    import time
    start_time = time.time()
    model = transformers.AutoModelForCausalLM.from_pretrained("webml-community/bonsai-webgpu")
    inputs = torch.tensor([[1, 2, 3]])
    output = model.generate(inputs)
    full_precision_time = (time.time() - start_time) * 1000
    start_time = time.time()
    model = transformers.AutoModelForCausalLM.from_pretrained("full-precision-model")
    inputs = torch.tensor([[1, 2, 3]])
    output = model.generate(inputs)
    ratio = full_precision_time / ((time.time() - start_time) * 1000)
    print(f"BENCHMARK:vs_full_precision_model_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_fail:compare_inference_speed:{e}")

# Test model against a suite of images from the LLaMA dataset
try:
    tracemalloc.start()
    import llama_dataset
    dataset = llama_dataset.load_dataset()
    start_time = time.time()
    model = transformers.AutoModelForCausalLM.from_pretrained("webml-community/bonsai-webgpu")
    for image in dataset:
        inputs = torch.tensor([image])
        output = model.generate(inputs)
    test_time = (time.time() - start_time) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:test_time_ms:{test_time:.2f}")
    print(f"BENCHMARK:test_memory_mb:{current / 1024 / 1024:.2f}")
    print(f"BENCHMARK:test_peak_memory_mb:{peak / 1024 / 1024:.2f}")
    print("TEST_PASS:test_against_llama_dataset")
except Exception as e:
    print(f"TEST_FAIL:test_against_llama_dataset:{e}")

# Compare performance vs the most similar baseline tool (DALL-E)
try:
    start_time = time.time()
    model = transformers.AutoModelForCausalLM.from_pretrained("dall-e")
    inputs = torch.tensor([[1, 2, 3]])
    output = model.generate(inputs)
    dall_e_time = (time.time() - start_time) * 1000
    start_time = time.time()
    model = transformers.AutoModelForCausalLM.from_pretrained("webml-community/bonsai-webgpu")
    inputs = torch.tensor([[1, 2, 3]])
    output = model.generate(inputs)
    bonsai_time = (time.time() - start_time) * 1000
    ratio = dall_e_time / bonsai_time
    print(f"BENCHMARK:vs_dall_e_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_FAIL:compare_performance_vs_dall_e:{e}")

print("RUN_OK")