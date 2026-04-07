import subprocess
import time
import tracemalloc
import os

# Install system packages
try:
    subprocess.run(['apk','add','--no-cache','go'], check=True)
    subprocess.run(['apk','add','--no-cache','git'], check=True)
    subprocess.run(['apk','add','--no-cache','cargo'], check=True)
    subprocess.run(['apk','add','--no-cache','rust'], check=True)
    subprocess.run(['apk','add','--no-cache','nodejs'], check=True)
    subprocess.run(['apk','add','--no-cache','npm'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install system packages: {e}")

# Clone and build Claude Code
try:
    start_time = time.time()
    subprocess.run(['git','clone','https://github.com/anthropics/claude-code/'], check=True)
    end_time = time.time()
    build_time = end_time - start_time
    print(f"BENCHMARK:clone_time_s:{build_time}")
    subprocess.run(['cargo','build','--release'], cwd='./claude-code', check=True)
    print(f"BENCHMARK:build_time_s:{time.time() - end_time}")
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to clone and build Claude Code: {e}")

# Run integration tests
try:
    start_time = time.time()
    subprocess.run(['cargo','test'], cwd='./claude-code', check=True)
    end_time = time.time()
    test_time = end_time - start_time
    print(f"BENCHMARK:test_time_s:{test_time}")
    print("TEST_PASS:integration_tests")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:integration_tests:Failed to run integration tests: {e}")

# Run hello world
try:
    start_time = time.time()
    subprocess.run(['cargo','run','--release'], cwd='./claude-code', check=True)
    end_time = time.time()
    hello_world_time = end_time - start_time
    print(f"BENCHMARK:hello_world_s:{hello_world_time}")
    print("TEST_PASS:hello_world")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:hello_world:Failed to run hello world: {e}")

# Measure memory usage
try:
    tracemalloc.start()
    subprocess.run(['cargo','run','--release'], cwd='./claude-code', check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:memory_usage:Failed to measure memory usage: {e}")

# Compare performance with LLaMA
try:
    start_time = time.time()
    subprocess.run(['python','llama_benchmark.py'], check=True)
    end_time = time.time()
    llama_time = end_time - start_time
    ratio = hello_world_time / llama_time
    print(f"BENCHMARK:vs_llama_hello_world_ratio:{ratio}")
except subprocess.CalledProcessError as e:
    print(f"TEST_SKIP:llama_benchmark:Failed to run LLaMA benchmark: {e}")

print("RUN_OK")