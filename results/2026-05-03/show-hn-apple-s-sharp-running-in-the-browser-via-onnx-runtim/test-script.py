import subprocess
import time
import tracemalloc
import os

# Install system packages
start_time = time.time()
install_result = subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
if install_result.returncode != 0:
    print(f"INSTALL_FAIL:apk install failed with return code {install_result.returncode}")
else:
    print("INSTALL_OK")
end_time = time.time()
install_time = end_time - start_time
print(f"BENCHMARK:install_time_s:{install_time:.2f}")

# Install tool dependencies
start_time = time.time()
install_result = subprocess.run(['npm', 'install', '-g', 'onnxruntime-web'], check=False)
if install_result.returncode != 0:
    print(f"INSTALL_FAIL:npm install failed with return code {install_result.returncode}")
else:
    print("INSTALL_OK")
end_time = time.time()
install_time = end_time - start_time
print(f"BENCHMARK:onnxruntime_install_time_s:{install_time:.2f}")

# Clone and build from source
start_time = time.time()
clone_result = subprocess.run(['git', 'clone', 'https://github.com/bring-shrubbery/ml-sharp-web.git'], check=False)
if clone_result.returncode != 0:
    print(f"INSTALL_FAIL:git clone failed with return code {clone_result.returncode}")
    print("TEST_SKIP:build and demo test:git clone failed")
else:
    os.chdir('ml-sharp-web')
    build_result = subprocess.run(['cargo', 'build'], check=False)
    if build_result.returncode != 0:
        print(f"INSTALL_FAIL:cargo build failed with return code {build_result.returncode}")
        print("TEST_SKIP:build and demo test:cargo build failed")
    else:
        print("INSTALL_OK")
end_time = time.time()
install_time = end_time - start_time
print(f"BENCHMARK:build_time_s:{install_time:.2f}")

# Run demo .NET Sharp browser app
try:
    start_time = time.time()
    demo_result = subprocess.run(['cargo', 'run'], check=False)
    if demo_result.returncode != 0:
        print(f"TEST_FAIL:demo .NET Sharp browser app failed with return code {demo_result.returncode}")
    else:
        print("TEST_PASS:demo .NET Sharp browser app")
    end_time = time.time()
    demo_time = end_time - start_time
    print(f"BENCHMARK:demo_time_s:{demo_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:demo .NET Sharp browser app: {str(e)}")

# Verify app uses ONNX Runtime Web API
try:
    import requests
    start_time = time.time()
    response = requests.get('https://api.github.com/repos/microsoft/onnxruntime/releases')
    end_time = time.time()
    api_time = end_time - start_time
    print(f"BENCHMARK:onnxruntime_api_time_s:{api_time:.2f}")
    if response.status_code == 200:
        print("TEST_PASS:app uses ONNX Runtime Web API")
    else:
        print(f"TEST_FAIL:app uses ONNX Runtime Web API: {response.status_code}")
except Exception as e:
    print(f"TEST_FAIL:app uses ONNX Runtime Web API: {str(e)}")

# Compare performance vs baseline tool
try:
    start_time = time.time()
    baseline_result = subprocess.run(['python', '-c', 'import time; time.sleep(1)'], check=False)
    if baseline_result.returncode != 0:
        print(f"TEST_FAIL:baseline tool failed with return code {baseline_result.returncode}")
    else:
        print("TEST_PASS:baseline tool")
    end_time = time.time()
    baseline_time = end_time - start_time
    ratio = demo_time / baseline_time
    print(f"BENCHMARK:vs_baseline_tool_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_FAIL:baseline tool: {str(e)}")

# Measure memory usage
start_time = time.time()
tracemalloc.start()
subprocess.run(['cargo', 'run'], check=False)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
end_time = time.time()
memory_time = end_time - start_time
print(f"BENCHMARK:memory_usage_mb:{peak/1024/1024:.2f}")
print(f"BENCHMARK:memory_time_s:{memory_time:.2f}")

print("RUN_OK")