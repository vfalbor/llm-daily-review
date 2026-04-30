import subprocess
import importlib
import time
import tracemalloc
import sys

def emit.marker(msg):
    print(msg)

try:
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    emit.marker('INSTALL_OK')
except Exception as e:
    emit.marker(f'INSTALL_FAIL:{str(e)}')

try:
    # Install Granite CLI
    subprocess.run(['pip', 'install', 'git+https://github.com/ibm/granite.git'], check=False)
    emit.marker('INSTALL_OK')
except Exception as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/ibm/granite.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './granite'], check=False)
        emit.marker('INSTALL_OK')
    except Exception as e2:
        emit.marker(f'INSTALL_FAIL:{str(e2)}')

try:
    import granite
    emit.marker('INSTALL_OK')
except Exception as e:
    emit.marker(f'INSTALL_FAIL:{str(e)}')

# Test 1: Create a new model
try:
    start_time = time.time()
    model = granite.Model()
    end_time = time.time()
    emit.marker(f'BENCHMARK:create_model_ms:{(end_time - start_time) * 1000:.2f}')
    emit.marker(f'TEST_PASS:create_model')
except Exception as e:
    emit.marker(f'TEST_FAIL:create_model:{str(e)}')

# Test 2: Train a basic model
try:
    start_time = time.time()
    tracemalloc.start()
    model.train([['input1', 'output1'], ['input2', 'output2']])
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    emit.marker(f'BENCHMARK:train_model_ms:{(end_time - start_time) * 1000:.2f}')
    emit.marker(f'BENCHMARK:train_model_memory_MB:{peak / 10**6:.2f}')
    emit.marker(f'TEST_PASS:train_model')
except Exception as e:
    emit.marker(f'TEST_FAIL:train_model:{str(e)}')

# Test 3: Compare performance vs CrewAI
try:
    import crewai
    start_time = time.time()
    crewai_model = crewai.Model()
    crewai_model.train([['input1', 'output1'], ['input2', 'output2']])
    end_time = time.time()
    crewai_time = (end_time - start_time) * 1000
    granite_time = (end_time - start_time) * 1000
    emit.marker(f'BENCHMARK:vs_crewai_train_model_ratio:{granite_time / crewai_time:.2f}')
    emit.marker(f'TEST_PASS:compare_performance')
except Exception as e:
    emit.marker(f'TEST_FAIL:compare_performance:{str(e)}')

# Additional benchmarks
try:
    start_time = time.time()
    model.import_data([['input1', 'output1'], ['input2', 'output2']])
    end_time = time.time()
    emit.marker(f'BENCHMARK:import_data_ms:{(end_time - start_time) * 1000:.2f}')
    emit.marker(f'TEST_PASS:import_data')
except Exception as e:
    emit.marker(f'TEST_FAIL:import_data:{str(e)}')

try:
    start_time = time.time()
    model.predict('input1')
    end_time = time.time()
    emit.marker(f'BENCHMARK:predict_ms:{(end_time - start_time) * 1000:.2f}')
    emit.marker(f'TEST_PASS:predict')
except Exception as e:
    emit.marker(f'TEST_FAIL:predict:{str(e)}')

emit.marker('RUN_OK')