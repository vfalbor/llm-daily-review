import subprocess
import sys
import time
import tracemalloc
import importlib.util
import importlib.machinery
import numpy as np
from scipy.stats import norm

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:Failed to install git {str(e)}")

# Clone the repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/open-research-models/mushroom-hallucination-research.git'], check=True)
except Exception as e:
    print(f"INSTALL_FAIL:Failed to clone the repository {str(e)}")

# Install pip dependencies
try:
    subprocess.run(['pip', 'install', '-e', './mushroom-hallucination-research'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:Failed to install pip package {str(e)}")

# Load the module
spec = importlib.util.spec_from_file_location("mushroom_hallucination", "./mushroom-hallucination-research/mushroom_hallucination.py")
mushroom_hallucination = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mushroom_hallucination)

# Measure import time
start_time = time.time()
importlib.import_module("mushroom_hallucination")
import_time = time.time() - start_time
print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")

# Test data accuracy
try:
    data = np.random.normal(0, 1, 1000)
    result = mushroom_hallucination.analyze_data(data)
    if np.allclose(result, norm.cdf(data)):
        print("TEST_PASS:Data Accuracy")
    else:
        print("TEST_FAIL:Data Accuracy:Result does not match expected output")
except Exception as e:
    print(f"TEST_FAIL:Data Accuracy:{str(e)}")

# Test models on similar data
try:
    similar_data = np.random.normal(0, 1, 1000)
    result = mushroom_hallucination.analyze_data(similar_data)
    if np.allclose(result, norm.cdf(similar_data)):
        print("TEST_PASS:Similar Data")
    else:
        print("TEST_FAIL:Similar Data:Result does not match expected output")
except Exception as e:
    print(f"TEST_FAIL:Similar Data:{str(e)}")

# Check for publication bias
try:
    publication_bias = mushroom_hallucination.check_publication_bias()
    if publication_bias < 0.05:
        print("TEST_PASS:Publication Bias")
    else:
        print("TEST_FAIL:Publication Bias:Publication bias detected")
except Exception as e:
    print(f"TEST_FAIL:Publication Bias:{str(e)}")

# Measure core operation latency
start_time = time.time()
mushroom_hallucination.analyze_data(np.random.normal(0, 1, 1000))
operation_latency = time.time() - start_time
print(f"BENCHMARK:operation_latency_ms:{operation_latency*1000:.2f}")

# Measure memory usage
tracemalloc.start()
mushroom_hallucination.analyze_data(np.random.normal(0, 1, 1000))
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{peak/1024/1024:.2f}")

# Compare performance vs baseline tool (DeepMind)
try:
    import deepmind
    start_time = time.time()
    deepmind.analyze_data(np.random.normal(0, 1, 1000))
    deepmind_latency = time.time() - start_time
    ratio = operation_latency / deepmind_latency
    print(f"BENCHMARK:vs_deepmind_ratio:{ratio:.2f}")
except Exception as e:
    print(f"BENCHMARK:vs_deepmind_ratio:Failed to compare with DeepMind {str(e)}")

print("RUN_OK")