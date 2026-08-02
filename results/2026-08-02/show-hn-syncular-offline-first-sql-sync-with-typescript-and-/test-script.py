import subprocess
import time
import tracemalloc
import importlib
import os

# Install system packages with subprocess
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone and install syncular from source
try:
    subprocess.run(['git', 'clone', 'https://github.com/syncular/syncular.git'], check=False)
    os.chdir('syncular')
    subprocess.run(['pip', 'install', '-e', '.'], check=False)
    INSTALL_OK = True
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")
    INSTALL_OK = False

if INSTALL_OK:
    try:
        import syncular
        print("INSTALL_OK")
    except ImportError as e:
        print(f"INSTALL_FAIL:{str(e)}")

# Run a minimal functional test with synthetic data
try:
    start_time = time.time()
    syncular.connect()
    test_table = syncular.Table("test_table")
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:connect_latency_ms:{latency_ms:.2f}")
    print(f"TEST_PASS:connect_test")
except Exception as e:
    print(f"TEST_FAIL:connect_test:{str(e)}")

# Measure import time
try:
    importlib.import_module("syncular")
    import_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(import_time - start_time) * 1000:.2f}")
    print(f"TEST_PASS:import_test")
except Exception as e:
    print(f"TEST_FAIL:import_test:{str(e)}")

# Measure memory usage
try:
    tracemalloc.start()
    import syncular
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    tracemalloc.stop()
    print(f"TEST_PASS:memory_test")
except Exception as e:
    print(f"TEST_FAIL:memory_test:{str(e)}")

# Compare performance vs the most similar baseline tool
# Since no similar baseline tool is listed, we'll compare with a simple SQL execution
try:
    import sqlite3
    start_time = time.time()
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_table")
    end_time = time.time()
    sqlite_latency_ms = (end_time - start_time) * 1000
    ratio = latency_ms / sqlite_latency_ms
    print(f"BENCHMARK:vs_sqlite_latency_ms_ratio:{ratio:.2f}")
    print(f"TEST_PASS:baseline_test")
except Exception as e:
    print(f"TEST_FAIL:baseline_test:{str(e)}")

# Always print RUN_OK
print("RUN_OK")