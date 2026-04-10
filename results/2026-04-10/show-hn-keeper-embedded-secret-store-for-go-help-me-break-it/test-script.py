import subprocess
import time
import tracemalloc
import os
import sys

# Install git package
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:apk_install:{e}")
    sys.exit(1)
else:
    print("INSTALL_OK")

# Clone Keeper repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/agberohq/keeper.git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:git_clone:{e}")
    sys.exit(1)
else:
    print("INSTALL_OK")

# Install Keeper
try:
    subprocess.run(['pip', 'install', '-e', 'keeper'], cwd='keeper', check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:pip_install:{e}")
    sys.exit(1)
else:
    print("INSTALL_OK")

# Measure import time
start_time = time.time()
try:
    import keeper
except ImportError as e:
    print(f"TEST_FAIL:keeper_import:{e}")
else:
    import_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time:.2f}")
    print("TEST_PASS:keeper_import")

# Measure create secret latency
start_time = time.time()
try:
    keeper.create_secret("test_secret", "test_value")
except Exception as e:
    print(f"TEST_FAIL:create_secret:{e}")
else:
    latency = (time.time() - start_time) * 1000
    print(f"BENCHMARK:create_secret_ms:{latency:.2f}")
    print("TEST_PASS:create_secret")

# Measure retrieve secret latency
start_time = time.time()
try:
    keeper.retrieve_secret("test_secret")
except Exception as e:
    print(f"TEST_FAIL:retrieve_secret:{e}")
else:
    latency = (time.time() - start_time) * 1000
    print(f"BENCHMARK:retrieve_secret_ms:{latency:.2f}")
    print("TEST_PASS:retrieve_secret")

# Measure memory usage
tracemalloc.start()
keeper.create_secret("test_secret", "test_value")
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Compare performance vs baseline tool (python's built-in secrets)
try:
    import secrets
    start_time = time.time()
    secrets.token_bytes(16)
    baseline_latency = (time.time() - start_time) * 1000
    ratio = latency / baseline_latency
    print(f"BENCHMARK:vs_python_secrets_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_FAIL:baseline_comparison:{e}")

print("RUN_OK")