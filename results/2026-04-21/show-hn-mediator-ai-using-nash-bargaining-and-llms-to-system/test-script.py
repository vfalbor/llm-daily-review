import subprocess
import time
import tracemalloc
import importlib
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repo
try:
    subprocess.run(['git', 'clone', 'https://github.com/mediator-ai/mediator-ai.git'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:git_clone_failed:{str(e)}')

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', '-e', 'mediator-ai'], check=True)
    print('INSTALL_OK')
except Exception as e:
    try:
        subprocess.run(['pip', 'install', '-e', './mediator-ai'], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:pip_install_failed:{str(e)}')

# Measure import time
try:
    start_time = time.time()
    import mediator_ai
    import_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
except Exception as e:
    print(f'TEST_FAIL:import_test:{str(e)}')

# Measure performance
try:
    start_time = time.time()
    tracemalloc.start()
    # Run a minimal functional test with synthetic data
    mediator_ai.run_example()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    latency = (end_time - start_time) * 1000
    print(f'BENCHMARK:core_operation_latency_ms:{latency:.2f}')
    print(f'BENCHMARK:memory_peak_mb:{peak / 1024 / 1024:.2f}')
    print(f'BENCHMARK:memory_current_mb:{current / 1024 / 1024:.2f}')
except Exception as e:
    print(f'TEST_FAIL:performance_test:{str(e)}')

# Measure performance of the most similar baseline tool (LangChain)
try:
    import langchain
    start_time = time.time()
    langchain.example()
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f'BENCHMARK:vs_langchain_latency_ms:{latency:.2f}')
    print(f'BENCHMARK:vs_langchain_ratio:{latency / (end_time - start_time) * 1000:.2f}')
except Exception as e:
    print(f'TEST_FAIL:baseline_test:{str(e)}')

print('RUN_OK')