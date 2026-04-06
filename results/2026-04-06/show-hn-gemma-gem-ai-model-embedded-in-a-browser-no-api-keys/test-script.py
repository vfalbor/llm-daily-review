import importlib
import importlib.util
import importlib.machinery
import time
import os
import sys
import subprocess

# Install required packages
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gemma-gem"])
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")

# Load Gemma
try:
    spec = importlib.util.find_spec("gemma_gem")
    if spec is None:
        print("TEST_FAIL:gemma_import:Module not found")
    else:
        print("TEST_PASS:gemma_import")
except Exception as e:
    print(f"TEST_FAIL:gemma_import:{str(e)}")

# Test gemma integration with multiple models
try:
    import gemma_gem
    gemma_gem.load_model("model1")
    gemma_gem.load_model("model2")
    print("TEST_PASS:multiple_models")
except Exception as e:
    print(f"TEST_FAIL:multiple_models:{str(e)}")

# Embed model in a browser without cloud
try:
    import gemma_gem
    gemma_gem.embed_model("model1", "browser")
    print("TEST_PASS:embed_model")
except Exception as e:
    print(f"TEST_FAIL:embed_model:{str(e)}")

# Benchmark import time
start_time = time.time()
import gemma_gem
end_time = time.time()
import_time_ms = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time_ms}")

# Compare with similar tools
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain"])
    import langchain
    start_time = time.time()
    import langchain
    end_time = time.time()
    langchain_import_time_ms = (end_time - start_time) * 1000
    if import_time_ms < langchain_import_time_ms:
        print("BENCHMARK:vs_langchain:faster_import")
    else:
        print("BENCHMARK:vs_langchain:slower_import")
except Exception as e:
    print(f"BENCHMARK:vs_langchain:failed_to_compare:{str(e)}")

print("RUN_OK")