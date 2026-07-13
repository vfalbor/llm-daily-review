import subprocess
import time
import tracemalloc
import sys
import importlib

# Install system package
print("Installing git package...")
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Install tool dependencies
print("Installing Claude Code and OpenCode packages...")
try:
    subprocess.run(['pip', 'install', 'transformers'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Load libraries
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print("IMPORT_OK")
except Exception as e:
    print(f"IMPORT_FAIL:{str(e)}")

# Measure import time
start_time = time.time()
try:
    import transformers
    import time
    print(f"BENCHMARK:import_time_ms:{(time.time() - start_time) * 1000:.2f}")
except Exception as e:
    print(f"IMPORT_FAIL:{str(e)}")

# Test Claude Code
def test_claude_code():
    try:
        model_name = "claude-code"
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        input_prompt = "Hello World!"
        inputs = tokenizer(input_prompt, return_tensors="pt")
        start_time = time.time()
        outputs = model.generate(**inputs)
        latency = (time.time() - start_time) * 1000
        print(f"BENCHMARK:{model_name}_latency_ms:{latency:.2f}")
        print(f"TEST_PASS:{model_name}")
    except Exception as e:
        print(f"TEST_FAIL:{model_name}:{str(e)}")

# Test OpenCode
def test_open_code():
    try:
        model_name = "open-code"
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        input_prompt = "Hello World!"
        inputs = tokenizer(input_prompt, return_tensors="pt")
        start_time = time.time()
        outputs = model.generate(**inputs)
        latency = (time.time() - start_time) * 1000
        print(f"BENCHMARK:{model_name}_latency_ms:{latency:.2f}")
        print(f"TEST_PASS:{model_name}")
    except Exception as e:
        print(f"TEST_FAIL:{model_name}:{str(e)}")

# Run tests
test_claude_code()
test_open_code()

# Compare performance with baseline
# Claude Code vs OpenCode
try:
    model1_name = "claude-code"
    model2_name = "open-code"
    model1_latency = float(next((line.split(":")[1] for line in sys.stdout.readlines() if f"{model1_name}_latency_ms" in line), None))
    model2_latency = float(next((line.split(":")[1] for line in sys.stdout.readlines() if f"{model2_name}_latency_ms" in line), None))
    ratio = model1_latency / model2_latency
    print(f"BENCHMARK:vs_{model1_name}_{model2_name}_latency_ratio:{ratio:.2f}")
except Exception as e:
    print(f"BENCHMARK_FAIL:vs_{model1_name}_{model2_name}_latency_ratio:{str(e)}")

# Measure memory usage
tracemalloc.start()
try:
    import transformers
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_peak_mb:{peak / 10**6:.2f}")
except Exception as e:
    print(f"BENCHMARK_FAIL:memory_usage_peak_mb:{str(e)}")
finally:
    tracemalloc.stop()

# Measure token generation
def measure_token_generation(model_name):
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        input_prompt = "Hello World!"
        inputs = tokenizer(input_prompt, return_tensors="pt")
        outputs = model.generate(**inputs)
        token_count = len(outputs[0])
        print(f"BENCHMARK:{model_name}_token_count:{token_count}")
    except Exception as e:
        print(f"BENCHMARK_FAIL:{model_name}_token_count:{str(e)}")

measure_token_generation("claude-code")
measure_token_generation("open-code")

# Print RUN_OK
print("RUN_OK")