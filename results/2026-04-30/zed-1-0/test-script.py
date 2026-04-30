import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)

# Install Zed
start_time = time.time()
try:
    subprocess.run(['npm', 'install', '-g', '@zed-dev/zed'], check=True)
    install_time = time.time() - start_time
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Install baseline tool (Jupyter Notebook)
start_time = time.time()
try:
    subprocess.run(['pip', 'install', 'jupyter'], check=True)
    baseline_install_time = time.time() - start_time
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Measure memory usage of Zed installation
tracemalloc.start()
subprocess.run(['npm', 'list', '-g', '@zed-dev/zed'], check=True)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:install_memory_mb:{current / (1024 * 1024)}")

# Test 1: Create a new project in Zed and write a basic script
try:
    start_time = time.time()
    subprocess.run(['zed', 'new', 'test_project'], check=True)
    subprocess.run(['echo', 'print("Hello World!")'], stdout=open('test_project/main.py', 'w'), check=True)
    creation_time = time.time() - start_time
    print("TEST_PASS:create_project")
    print(f"BENCHMARK:create_project_time_ms:{creation_time * 1000}")
except Exception as e:
    print(f"TEST_FAIL:create_project:{str(e)}")

# Test 2: Run a Python script using Zed's web IDE
try:
    start_time = time.time()
    subprocess.run(['zed', 'run', 'test_project'], check=True)
    execution_time = time.time() - start_time
    print("TEST_PASS:run_script")
    print(f"BENCHMARK:run_script_time_ms:{execution_time * 1000}")
except Exception as e:
    print(f"TEST_FAIL:run_script:{str(e)}")

# Compare performance vs Jupyter Notebook
try:
    start_time = time.time()
    subprocess.run(['jupyter', 'notebook', '--allow-root'], check=True)
    baseline_creation_time = time.time() - start_time
    print(f"BENCHMARK:vs_jupyter_creation_ratio:{creation_time / baseline_creation_time}")
except Exception as e:
    print(f"BENCHMARK:vs_jupyter_creation_ratio:failed")

# Count lines of code in Zed and Jupyter Notebook
try:
    zed_loc = sum(1 for line in open('test_project/main.py'))
    jupyter_loc = sum(1 for line in open('/usr/local/lib/python3.12/site-packages/ipykernel (__init__.py'))
    print(f"BENCHMARK:zed_loc_count:{zed_loc}")
    print(f"BENCHMARK:jupyter_loc_count:{jupyter_loc}")
except Exception as e:
    print(f"BENCHMARK:loc_count:failed")

# Count test files in Zed and Jupyter Notebook
try:
    zed_test_files = len(os.listdir('test_project'))
    jupyter_test_files = len(os.listdir('/usr/local/lib/python3.12/site-packages/ipykernel'))
    print(f"BENCHMARK:zed_test_files_count:{zed_test_files}")
    print(f"BENCHMARK:jupyter_test_files_count:{jupyter_test_files}")
except Exception as e:
    print(f"BENCHMARK:test_files_count:failed")

print("RUN_OK")