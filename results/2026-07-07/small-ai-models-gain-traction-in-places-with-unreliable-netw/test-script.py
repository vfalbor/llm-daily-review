import subprocess
import sys
import time
import tracemalloc
import importlib

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Try installing package with pip, fall back to git clone if fails
try:
    subprocess.run(['pip', 'install', 'transformers'], check=True)
    INSTALL_OK = True
except subprocess.CalledProcessError:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/huggingface/transformers.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './transformers'], cwd='./transformers', check=True)
        IMPORT_OK = True
    except subprocess.CalledProcessError:
        IMPORT_OK = False
        print('INSTALL_FAIL:Failed to install package')

# Import the installed package and measure import time
start_time = time.time()
try:
    import transformers
    import_time = time.time() - start_time
    BENCHMARK = f'BENCHMARK:import_time_ms:{import_time * 1000}'
    print(BENCHMARK)
    TEST_PASS_NAME = 'Import Test'
    print(f'TEST_PASS:{TEST_PASS_NAME}')
except Exception as e:
    print(f'TEST_FAIL:Import Test:{str(e)}')

# Run a minimal functional test with synthetic data
try:
    # Measure core operation latency
    start_time = time.time()
    model = transformers.pipeline('sentiment-analysis')
    result = model('This is a test sentence')
    latency = time.time() - start_time
    BENCHMARK = f'BENCHMARK:core_operation_latency_ms:{latency * 1000}'
    print(BENCHMARK)
    TEST_PASS_NAME = 'Core Operation Test'
    print(f'TEST_PASS:{TEST_PASS_NAME}')
except Exception as e:
    print(f'TEST_FAIL:Core Operation Test:{str(e)}')

# Measure memory usage
tracemalloc.start()
model = transformers.pipeline('sentiment-analysis')
result = model('This is a test sentence')
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
BENCHMARK = f'BENCHMARK:memory_usage_MB:{current / (1024 * 1024)}'
print(BENCHMARK)

# Compare performance vs similar tool (e.g. spaCy)
try:
    import spacy
    spacy_model = spacy.load('en_core_web_sm')
    spacy_start_time = time.time()
    spacy_result = spacy_model('This is a test sentence')
    spacy_latency = time.time() - spacy_start_time
    ratio = latency / spacy_latency
    BENCHMARK = f'BENCHMARK:vs_spacy_latency_ratio:{ratio}'
    print(BENCHMARK)
except Exception as e:
    print(f'TEST_SKIP:SpaCy Comparison Test:{str(e)}')

# Print final RUN_OK message
print('RUN_OK')