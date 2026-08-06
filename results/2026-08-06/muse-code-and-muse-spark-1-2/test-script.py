import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

# Install system packages
print("Installing system packages...")
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install Muse Code CLI
print("Installing Muse Code CLI...")
try:
    subprocess.run(['pip', 'install', 'muse-code'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")

    # Fallback to git clone + pip install -e
    try:
        subprocess.run(['git', 'clone', 'https://github.com/meta-ai/muse-code.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './muse-code'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

# Import Muse Code and measure import time
import_start = time.time()
try:
    spec = importlib.util.find_spec('muse')
    if spec is not None:
        importlib.machinery.ModuleSpec(spec).loader.exec_module(spec)
    else:
        raise Exception("Muse Code not found")
except Exception as e:
    print(f"TEST_FAIL:import: {str(e)}")

import_end = time.time()
import_time = (import_end - import_start) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Create a new Muse Code project
try:
    subprocess.run(['muse', 'init', 'test-project'], check=True)
    print("TEST_PASS:create_project")
except Exception as e:
    print(f"TEST_FAIL:create_project: {str(e)}")

# Write a simple AI model using Muse Code's API
try:
    with open('test-project/model.py', 'w') as f:
        f.write("import muse\n\nclass MyModel(muse.Model):\n    def forward(self, x):\n        return x")
    print("TEST_PASS:write_model")
except Exception as e:
    print(f"TEST_FAIL:write_model: {str(e)}")

# Test model accuracy using the Muse Code testing framework
try:
    subprocess.run(['muse', 'test', 'test-project'], check=True)
    print("TEST_PASS:test_model")
except Exception as e:
    print(f"TEST_FAIL:test_model: {str(e)}")

# Compare Muse Code's performance with other research platforms
try:
    # Measure time to run a simple model
    tracemalloc.start()
    start = time.time()
    subprocess.run(['muse', 'run', 'test-project'], check=True)
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    muse_time = (end - start) * 1000
    muse_memory = current / (1024 * 1024)  # Convert to MB
    print(f"BENCHMARK:muse_time_ms:{muse_time}")
    print(f"BENCHMARK:muse_memory_mb:{muse_memory}")

    # Measure time to run a similar model in LLM Studio
    subprocess.run(['pip', 'install', 'llm-studio'], check=True)
    import llm_studio
    start = time.time()
    llm_studio.run()
    end = time.time()
    llm_time = (end - start) * 1000
    print(f"BENCHMARK:llm_time_ms:{llm_time}")
    print(f"BENCHMARK:vs_llm_time_ratio:{muse_time / llm_time}")
except Exception as e:
    print(f"TEST_FAIL:compare_performance: {str(e)}")

# Count lines of code in the project
try:
    loc_count = 0
    for root, dirs, files in os.walk('test-project'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += len(f.readlines())
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    print(f"TEST_FAIL:loc_count: {str(e)}")

# Count test files in the project
try:
    test_files_count = 0
    for root, dirs, files in os.walk('test-project'):
        for file in files:
            if file.startswith('test_'):
                test_files_count += 1
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    print(f"TEST_FAIL:test_files_count: {str(e)}")

print("RUN_OK")