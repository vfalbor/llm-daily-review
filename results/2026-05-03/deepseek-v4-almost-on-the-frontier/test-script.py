import subprocess
import time
import tracemalloc
import importlib.util
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'deepseek'], check=True)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:deepseek")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/simonw/deepseek.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './deepseek'], check=True, cwd='./deepseek')
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:deepseek_fallback")
        sys.exit(1)
else:
    print("INSTALL_OK")

# Import the package and measure import time
start_time = time.time()
spec = importlib.util.find_spec('deepseek')
end_time = time.time()
import_time_ms = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time_ms}")

# Test the model's ability to answer complex questions
try:
    import deepseek
    start_time = time.time()
    model = deepseek.Model()
    answer = model.answer("What is the meaning of life?")
    end_time = time.time()
    query_latency_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:query_latency_ms:{query_latency_ms}")
    print("TEST_PASS:complex_question")
except Exception as e:
    print(f"TEST_FAIL:complex_question:{str(e)}")

# Evaluate the model's performance in a conversational setting
try:
    import deepseek
    start_time = time.time()
    model = deepseek.Model()
    answer1 = model.answer("How are you?")
    answer2 = model.answer("I'm good, thanks. How are you?")
    end_time = time.time()
    conversational_latency_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:conversational_latency_ms:{conversational_latency_ms}")
    print("TEST_PASS:conversational_setting")
except Exception as e:
    print(f"TEST_FAIL:conversational_setting:{str(e)}")

# Compare the model's performance to LangChain
try:
    import langchain
    import deepseek
    start_time = time.time()
    langchain_model = langchain.Model()
    deepseek_model = deepseek.Model()
    answer1 = langchain_model.answer("What is the meaning of life?")
    answer2 = deepseek_model.answer("What is the meaning of life?")
    end_time = time.time()
    langchain_latency_ms = (end_time - start_time) * 1000
    ratio = (query_latency_ms / langchain_latency_ms)
    print(f"BENCHMARK:vs_langchain_query_latency_ratio:{ratio}")
    print("TEST_PASS:langchain_comparison")
except Exception as e:
    print(f"TEST_FAIL:langchain_comparison:{str(e)}")

# Measure memory usage
tracemalloc.start()
import deepseek
model = deepseek.Model()
memory_usage, peak_memory_usage = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{memory_usage / (1024 * 1024)}")
print(f"BENCHMARK:peak_memory_usage_mb:{peak_memory_usage / (1024 * 1024)}")

# Measure time to perform 100 queries
start_time = time.time()
import deepseek
model = deepseek.Model()
for _ in range(100):
    model.answer("What is the meaning of life?")
end_time = time.time()
time_to_perform_queries_s = end_time - start_time
print(f"BENCHMARK:time_to_perform_queries_s:{time_to_perform_queries_s}")

# Measure number of lines of code
import os
loc_count = sum(1 for file in os.listdir('./deepseek') if file.endswith('.py') for line in open(os.path.join('./deepseek', file), 'r'))
print(f"BENCHMARK:loc_count:{loc_count}")

# Measure number of test files
import os
test_files_count = sum(1 for file in os.listdir('./deepseek/tests') if file.endswith('.py'))
print(f"BENCHMARK:test_files_count:{test_files_count}")

print("RUN_OK")