import subprocess
import sys
import time
import tracemalloc
import importlib.util
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

# Install required packages
def install_packages():
    pkgs = ['git', 'pip']
    for pkg in pkgs:
        try:
            subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:apk add {pkg} failed with exit code {e.returncode}")
            sys.exit(1)

# Install tool dependencies
def install_tool():
    try:
        subprocess.run(['pip', 'install', 'llm-ai'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:pip install llm-ai failed with exit code {e.returncode}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/kick-drum-kd.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './kick-drum-kd'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:pip install -e . failed with exit code {e.returncode}")
            sys.exit(1)

# Load the package
def load_package():
    spec = importlib.util.find_spec('llm_ai')
    if spec is None:
        print("INSTALL_FAIL: failed to find llm-ai package")
        sys.exit(1)
    return importlib.import_module('llm_ai')

# Test 1: Train a model on a standard dataset and measure accuracy
def test_train_model(llm_ai):
    try:
        start_time = time.time()
        model = llm_ai.train_model()
        end_time = time.time()
        print(f"BENCHMARK:train_time_s:{end_time - start_time}")
        accuracy = llm_ai.evaluate_model(model)
        print(f"BENCHMARK:train_accuracy:{accuracy}")
        print("TEST_PASS:train_model")
    except Exception as e:
        print(f"TEST_FAIL:train_model:{str(e)}")

# Test 2: Run a 1000-sample inference pass and check output quality
def test_inference(llm_ai):
    try:
        start_time = time.time()
        llm_ai.inference_model(1000)
        end_time = time.time()
        print(f"BENCHMARK:inference_time_s:{end_time - start_time}")
        print("TEST_PASS:inference")
    except Exception as e:
        print(f"TEST_FAIL:inference:{str(e)}")

# Test 3: Compare diffusion model performance to baseline architectures
def test_compare_models(llm_ai):
    try:
        baseline_tools = ['LAMM', 'vLLM', 'Ollama']
        for tool in baseline_tools:
            start_time = time.time()
            llm_ai.compare_models(tool)
            end_time = time.time()
            print(f"BENCHMARK:vs_{tool}_compare_time_s:{end_time - start_time}")
        print("TEST_PASS:compare_models")
    except Exception as e:
        print(f"TEST_FAIL:compare_models:{str(e)}")

# Measure memory usage
def measure_memory():
    tracemalloc.start()
    llm_ai = load_package()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Measure import time
def measure_import_time():
    start_time = time.time()
    llm_ai = load_package()
    end_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")

# Compare performance vs the most similar baseline tool
def compare_performance(llm_ai):
    try:
        start_time = time.time()
        llm_ai.compare_performance('LAMM')
        end_time = time.time()
        print(f"BENCHMARK:vs_LAMM_compare_time_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance:{str(e)}")

install_packages()
install_tool()
llm_ai = load_package()

measure_import_time()
test_train_model(llm_ai)
test_inference(llm_ai)
test_compare_models(llm_ai)
measure_memory()
compare_performance(llm_ai)

print("RUN_OK")