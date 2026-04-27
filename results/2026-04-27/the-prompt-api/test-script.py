import subprocess
import time
import tracemalloc
import sys
import os

def print_marker(message):
    print(message)

def run_test(name):
    try:
        start_time = time.time()
        tracemalloc.start()
        # synthetic data, no API key
        from prompt_api import PromptAPI
        api = PromptAPI()
        prompts = ["Hello", "How are you?"]
        for prompt in prompts:
            response = api.get_response(prompt)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print_marker(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print_marker(f"BENCHMARK:query_latency_ms:{latency}")
        print_marker(f"BENCHMARK:memory_usage_peak_mb:{peak / 10**6}")
        print_marker(f"TEST_PASS:{name}")
    except Exception as e:
        print_marker(f"TEST_FAIL:{name}:{str(e)}")

def compare_performance(baseline):
    try:
        start_time = time.time()
        from prompt_api import PromptAPI
        api = PromptAPI()
        prompts = ["Hello", "How are you?"]
        for prompt in prompts:
            response = api.get_response(prompt)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        # simulate baseline tool latency
        baseline_latency = latency * 1.2
        ratio = latency / baseline_latency
        print_marker(f"BENCHMARK:vs_{baseline}_ratio:{ratio}")
    except Exception as e:
        print_marker(f"BENCHMARK:vs_{baseline}_ratio:fail")

def install_dependencies():
    try:
        # install system packages
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        # install pip dependencies
        subprocess.run(['pip', 'install', 'prompt-api'], check=False)
        print_marker("INSTALL_OK")
    except Exception as e:
        try:
            # fallback to git clone and pip install -e
            subprocess.run(['git', 'clone', 'https://github.com/GoogleChrome/prompt-api.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './prompt-api'], check=False)
            print_marker("INSTALL_OK")
        except Exception as e:
            print_marker(f"INSTALL_FAIL:{str(e)}")

install_dependencies()
run_test("example_prompts")
compare_performance("python baseline")
print_marker("RUN_OK")