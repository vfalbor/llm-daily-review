import subprocess
import sys
import time
import tracemalloc
from qwen_model import Qwen

def install_packages(package):
    subprocess.run(['apk', 'add', '--no-cache', package], check=False)

def install_tool_dependencies(tool, method):
    if method == 'pip':
        subprocess.run(['pip', 'install', tool], check=False)
    elif method == 'git':
        subprocess.run(['git', 'clone', tool], check=False)
        subprocess.run(['pip', 'install', '-e', '.'], check=False, cwd='./qwen-model')

def print_marker(marker, name=None, reason=None, value=None):
    if name:
        if reason:
            print(f"{marker}:{name}:{reason}", flush=True)
        else:
            print(f"{marker}:{name}", flush=True)
    elif value:
        print(f"{marker}:{value}", flush=True)
    else:
        print(f"{marker}", flush=True)

def test_qwen():
    try:
        model = Qwen()
        input_text = "Hello, World!"
        output = model(input_text)
        if output:
            print_marker("TEST_PASS", "qwen_test")
        else:
            print_marker("TEST_FAIL", "qwen_test", "Model output is empty")
    except Exception as e:
        print_marker("TEST_FAIL", "qwen_test", str(e))

def compare_with_baseline():
    try:
        import bloom
        start_time = time.time()
        bloom_model = bloom.Bloom()
        input_text = "Hello, World!"
        output = bloom_model(input_text)
        end_time = time.time()
        bloom_latency = (end_time - start_time) * 1000
        start_time = time.time()
        qwen_model = Qwen()
        output = qwen_model(input_text)
        end_time = time.time()
        qwen_latency = (end_time - start_time) * 1000
        ratio = qwen_latency / bloom_latency
        print_marker("BENCHMARK", f"vs_bloom_latency_ratio", value=ratio)
    except Exception as e:
        print_marker("TEST_FAIL", "baseline_test", str(e))

def stress_test():
    try:
        model = Qwen()
        input_text = "Hello, World!"
        start_time = time.time()
        for _ in range(100):
            output = model(input_text)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print_marker("BENCHMARK", f"stress_test_latency", value=latency)
    except Exception as e:
        print_marker("TEST_FAIL", "stress_test", str(e))

def main():
    install_packages('git')
    install_tool_dependencies('qwen-model', 'git')
    try:
        start_time = time.time()
        import qwen_model
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print_marker("BENCHMARK", f"import_time", value=import_time)
    except Exception as e:
        print_marker("INSTALL_FAIL", reason=str(e))
        return

    print_marker("INSTALL_OK")
    test_qwen()
    compare_with_baseline()
    stress_test()

    tracemalloc.start()
    model = Qwen()
    input_text = "Hello, World!"
    output = model(input_text)
    current, peak = tracemalloc.get_traced_memory()
    print_marker("BENCHMARK", f"memory_usage", value=current)
    print_marker("BENCHMARK", f"memory_peak", value=peak)
    tracemalloc.stop()

    print_marker("RUN_OK")

if __name__ == "__main__":
    main()