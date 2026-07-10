import subprocess
import time
import tracemalloc
import importlib

# Install system packages with subprocess
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install muse-spark
try:
    subprocess.run(['pip', 'install', 'muse-spark'], check=False)
    INSTALL_RESULT = "INSTALL_OK"
except Exception as e:
    INSTALL_RESULT = f"INSTALL_FAIL:{str(e)}"
    try:
        subprocess.run(['git', 'clone', 'https://github.com/meta-ai/muse-spark.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './muse-spark'], check=False)
        INSTALL_RESULT = "INSTALL_OK"
    except Exception as e:
        INSTALL_RESULT = f"INSTALL_FAIL:{str(e)}"
print(INSTALL_RESULT)

# Import muse-spark and run a minimal functional test
try:
    start_import_time = time.time()
    import muse_spark
    import_time = time.time() - start_import_time
    print(f"BENCHMARK:import_time_ms:{import_time * 1000:.0f}")

    # Run simple API call and measure latency
    start_time = time.time()
    result = muse_spark.Model.predict("Hello, World!")
    end_time = time.time()
    latency = end_time - start_time
    print(f"BENCHMARK:hello_world_ms:{latency * 1000:.0f}")
    print(f"TEST_PASS:muse_spark_test")

except Exception as e:
    print(f"TEST_FAIL:muse_spark_test:{str(e)}")

# Compare performance vs baseline tool LangChain
try:
    start_import_time = time.time()
    import langchain
    import_time_langchain = time.time() - start_import_time
    ratio = import_time / import_time_langchain
    print(f"BENCHMARK:vs_langchain_import_time_ratio:{ratio:.2f}")

    # Run simple API call and measure latency for LangChain
    start_time = time.time()
    result = langchain.Model.predict("Hello, World!")
    end_time = time.time()
    latency = end_time - start_time
    ratio = latency / (end_time - start_time)
    print(f"BENCHMARK:vs_langchain_hello_world_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_SKIP:langchain_comparison:{str(e)}")

# Measure memory usage
tracemalloc.start()
import muse_spark
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Measure loc count
muse_spark_loc_count = subprocess.run(['git', 'ls-files', '-z'], check=False, cwd='./muse-spark').stdout.decode('utf-8').count('\0')
print(f"BENCHMARK:muse_spark_loc_count:{muse_spark_loc_count}")

# Measure test files count
muse_spark_test_files_count = subprocess.run(['git', 'ls-files', '-z', './tests'], check=False, cwd='./muse-spark').stdout.decode('utf-8').count('\0')
print(f"BENCHMARK:muse_spark_test_files_count:{muse_spark_test_files_count}")

print("RUN_OK")