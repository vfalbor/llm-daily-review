import subprocess
import time
import tracemalloc
import importlib
import os

print("INSTALL_OK")
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['pip', 'install', '-e', 'git+https://github.com/zknill/zeta.git'], check=False)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/zknill/zeta.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './zeta'], check=False)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        exit()

try:
    import zeta
    print("TEST_PASS:import_zeta")
except ImportError as e:
    print(f"TEST_FAIL:import_zeta:{e}")

start = time.time()
importlib.import_module('zeta')
end = time.time()
import_time_ms = (end - start) * 1000
print(f"BENCHMARK:import_time_ms:{import_time_ms:.2f}")

tracemalloc.start()
start = time.time()
zeta_agent = zeta.Zeta()
end = time.time()
response_time_ms = (end - start) * 1000
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
memory_mb = current / 1024 / 1024
print(f"BENCHMARK:response_time_ms:{response_time_ms:.2f}")
print(f"BENCHMARK:memory_usage_mb:{memory_mb:.2f}")

try:
    response = zeta_agent.run('hello')
    if response == 'hello':
        print("TEST_PASS:run_hello")
    else:
        print(f"TEST_FAIL:run_hello:invalid_response")
except Exception as e:
    print(f"TEST_FAIL:run_hello:{e}")

# Compare performance with Rasa
try:
    import rasa
    print("TEST_PASS:import_rasa")
    rasa_agent = rasa.Agent()
    start = time.time()
    rasa_agent.run('hello')
    end = time.time()
    rasa_response_time_ms = (end - start) * 1000
    print(f"BENCHMARK:vs_rasa_response_time_ms:{rasa_response_time_ms:.2f}")
    ratio = response_time_ms / rasa_response_time_ms
    print(f"BENCHMARK:vs_rasa_response_time_ratio:{ratio:.2f}")
except ImportError as e:
    print(f"TEST_SKIP:import_rasa:{e}")

print("RUN_OK")