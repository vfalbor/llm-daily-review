import subprocess
import time
import tracemalloc
import importlib.util
import sys

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['pip', 'install', 'git+https://github.com/some-repo/hybrid-attention'], check=False)

try:
    subprocess.run(['pip', 'install', 'transformer-xl'], check=False)
except subprocess.CalledProcessError:
    subprocess.run(['git', 'clone', 'https://github.com/some-repo/transformer-xl'], check=False)
    subprocess.run(['pip', 'install', '-e', './transformer-xl'], check=False)

try:
    # Import Hybrid Attention
    spec = importlib.util.find_spec('hybrid_attention')
    if spec is None:
        print("INSTALL_FAIL:Hybrid Attention import failed")
        sys.exit(1)
    hybrid_attention = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hybrid_attention)
except Exception as e:
    print(f"INSTALL_FAIL:Hybrid Attention import failed:{str(e)}")
    sys.exit(1)

# Measure import time
import_time = time.time()
try:
    import hybrid_attention
except Exception as e:
    print(f"TEST_FAIL:Import Hybrid Attention:{str(e)}")
else:
    import_time_taken = time.time() - import_time
    print(f"BENCHMARK:import_time_ms:{import_time_taken*1000:.2f}")

# Synthetic data for testing
synthetic_data = ["This is a test sentence", "This is another test sentence"]

# Run a minimal functional test with synthetic data
test_start_time = time.time()
try:
    model = hybrid_attention.HybridAttentionModel()
    output = model(synthetic_data)
except Exception as e:
    print(f"TEST_FAIL:Hybrid Attention test failed:{str(e)}")
else:
    test_time_taken = time.time() - test_start_time
    print(f"TEST_PASS:Hybrid Attention test passed")
    print(f"BENCHMARK:hybrid_attention_test_ms:{test_time_taken*1000:.2f}")

# Compare performance vs Transformer-XL
try:
    import transformer_xl
except Exception as e:
    print(f"INSTALL_FAIL:Transformer-XL import failed:{str(e)}")
else:
    transformer_xl_start_time = time.time()
    try:
        model = transformer_xl.TransformerXLModel()
        output = model(synthetic_data)
    except Exception as e:
        print(f"TEST_FAIL:Transformer-XL test failed:{str(e)}")
    else:
        transformer_xl_time_taken = time.time() - transformer_xl_start_time
        print(f"TEST_PASS:Transformer-XL test passed")
        ratio = (test_time_taken / transformer_xl_time_taken)
        print(f"BENCHMARK:vs_transformer_xl_ratio:{ratio:.2f}")

# Measure memory usage
tracemalloc.start()
model = hybrid_attention.HybridAttentionModel()
output = model(synthetic_data)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{current/1024/1024:.2f}")
print(f"BENCHMARK:peak_memory_usage_mb:{peak/1024/1024:.2f}")

# Count lines of code
loc_count = 0
with open(__file__, 'r') as f:
    for line in f:
        loc_count += 1
print(f"BENCHMARK:loc_count:{loc_count}")

print("RUN_OK")