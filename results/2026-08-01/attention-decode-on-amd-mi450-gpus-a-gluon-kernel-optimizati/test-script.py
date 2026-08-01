import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

def install_package(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=False)
    except Exception as e:
        print(f"INSTALL_FAIL:apk {package} failed: {e}")

def install_tool_dependencies(package):
    try:
        subprocess.run(['pip', 'install', package], check=False)
    except Exception as e:
        print(f"INSTALL_FAIL:pip {package} failed: {e}")

def run_test(name):
    try:
        # Load the module dynamically
        spec = importlib.util.find_spec(name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        start_time = time.time()
        # Test the module
        module.test_minimal_functional_test()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:{name}_latency_ms:{latency}")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")

def run_benchmark(name):
    try:
        # Load the module dynamically
        spec = importlib.util.find_spec(name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        start_time = time.time()
        # Run the benchmark
        module.run_benchmark()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:{name}_benchmark_ms:{latency}")
    except Exception as e:
        print(f"BENCHMARK:{name}_benchmark_ms:_failed")

def compare_with_baseline(package):
    try:
        # Load the baseline module dynamically
        baseline_spec = importlib.util.find_spec(package)
        baseline_module = importlib.util.module_from_spec(baseline_spec)
        baseline_spec.loader.exec_module(baseline_module)
        
        # Run the baseline benchmark
        start_time = time.time()
        baseline_module.run_benchmark()
        end_time = time.time()
        baseline_latency = (end_time - start_time) * 1000
        
        # Run our package's benchmark
        start_time = time.time()
        importlib.import_module('gluon_attention_decode').run_benchmark()
        end_time = time.time()
        our_latency = (end_time - start_time) * 1000
        
        ratio = our_latency / baseline_latency
        print(f"BENCHMARK:vs_{package}_ratio:{ratio}")
    except Exception as e:
        print(f"BENCHMARK:vs_{package}_ratio:failed")

def measure_memory():
    tracemalloc.start()
    import gluon_attention_decode
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    tracemalloc.stop()

def measure_import_time():
    start_time = time.time()
    import gluon_attention_decode
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{latency}")

def measure_install_time():
    start_time = time.time()
    install_tool_dependencies('gluon-attention-decode')
    end_time = time.time()
    latency = (end_time - start_time)
    print(f"BENCHMARK:install_time_s:{latency}")

# Install required packages
install_package('git')

# Install the package
install_tool_dependencies('gluon-attention-decode')

# Measure install time
measure_install_time()

# Measure import time
measure_import_time()

# Measure memory usage
measure_memory()

# Run tests
run_test('gluon_attention_decode')
run_benchmark('gluon_attention_decode')
compare_with_baseline('tensorflow')

# Run additional tests
try:
    import tensorflow
    run_benchmark('tensorflow')
except Exception as e:
    print(f"TEST_FAIL:tensorflow:{e}")

try:
    import torch
    run_benchmark('torch')
except Exception as e:
    print(f"TEST_FAIL:torch:{e}")

print("RUN_OK")