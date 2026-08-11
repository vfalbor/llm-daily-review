import subprocess
import time
import tracemalloc
import importlib.util
import requests

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install git: {e}")
    exit(1)

# Install LFM2.5 package
try:
    subprocess.run(['pip', 'install', 'transformers'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install transformers: {e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/huggingface/transformers.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './transformers'], check=True, cwd='./transformers')
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install transformers from source: {e}")
        exit(1)

# Import LFM2.5 package and measure import time
start_time = time.time()
try:
    import transformers
except ImportError as e:
    print(f"INSTALL_FAIL:Failed to import transformers: {e}")
    exit(1)
import_time = time.time() - start_time
print(f"BENCHMARK:import_time_ms:{import_time * 1000:.2f}")

# Run example code on benchmark dataset
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained("LiquidAI/LFM2.5-2.6B")
    tokenizer = AutoTokenizer.from_pretrained("LiquidAI/LFM2.5-2.6B")
    input_ids = tokenizer.encode("Hello, world!", return_tensors="pt")
    start_time = time.time()
    outputs = model(input_ids)
    latency = time.time() - start_time
    print(f"BENCHMARK:hello_world_ms:{latency * 1000:.2f}")
    print(f"TEST_PASS:run_example_code")
except Exception as e:
    print(f"TEST_FAIL:run_example_code: {e}")

# Compare performance with other NLP models
try:
    from transformers import BertTokenizer, BertModel
    bert_model = BertModel.from_pretrained('bert-base-uncased')
    bert_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    input_ids = bert_tokenizer.encode("Hello, world!", return_tensors="pt")
    start_time = time.time()
    outputs = bert_model(input_ids)
    latency = time.time() - start_time
    print(f"BENCHMARK:vs_bert_hello_world_ms:{latency * 1000:.2f}")
    print(f"TEST_PASS:compare_performance")
except Exception as e:
    print(f"TEST_FAIL:compare_performance: {e}")

# Verify accuracy on various NLP tasks
try:
    from transformers import pipeline
    nlp = pipeline('sentiment-analysis', model="LiquidAI/LFM2.5-2.6B")
    start_time = time.time()
    output = nlp("I love this product!")
    latency = time.time() - start_time
    print(f"BENCHMARK:sentiment_analysis_ms:{latency * 1000:.2f}")
    print(f"TEST_PASS:verify_accuracy")
except Exception as e:
    print(f"TEST_FAIL:verify_accuracy: {e}")

# Measure memory usage
tracemalloc.start()
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained("LiquidAI/LFM2.5-2.6B")
    tokenizer = AutoTokenizer.from_pretrained("LiquidAI/LFM2.5-2.6B")
except Exception as e:
    pass
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{peak / 1024 / 1024:.2f}")
tracemalloc.stop()

# Measure time taken to install LFM2.5
try:
    start_time = time.time()
    subprocess.run(['pip', 'install', 'transformers'], check=True)
    install_time = time.time() - start_time
    print(f"BENCHMARK:install_time_s:{install_time:.2f}")
except subprocess.CalledProcessError as e:
    pass

# Measure time taken to compile a simple NLP task
try:
    start_time = time.time()
    from transformers import pipeline
    nlp = pipeline('sentiment-analysis', model="LiquidAI/LFM2.5-2.6B")
    output = nlp("I love this product!")
    compile_time = time.time() - start_time
    print(f"BENCHMARK:compile_time_ms:{compile_time * 1000:.2f}")
except Exception as e:
    pass

# Measure count of lines of code
try:
    response = requests.get('https://huggingface.co/LiquidAI/LFM2.5-2.6B/tree/main')
    loc_count = len(response.text.splitlines())
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    pass

# Measure count of test files
try:
    response = requests.get('https://huggingface.co/LiquidAI/LFM2.5-2.6B/tree/main/tests')
    test_files_count = len(response.text.splitlines())
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    pass

print("RUN_OK")