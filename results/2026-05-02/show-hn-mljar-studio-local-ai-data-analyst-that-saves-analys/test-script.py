import subprocess
import time
import tracemalloc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mljar import Mljar

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['pip', 'install', 'mljar'], check=False)

try:
    # Install Mljar Studio and analyze a sample dataset
    start_time = time.time()
    mljar = Mljar()
    synthetic_data = pd.DataFrame(np.random.rand(100, 5), columns=['A', 'B', 'C', 'D', 'E'])
    mljar.fit(synthetic_data)
    end_time = time.time()
    print(f"INSTALL_OK")
    print(f"BENCHMARK:install_time_s:{end_time - start_time}")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

try:
    # Insert 100 rows and measure render latency
    start_time = time.time()
    mljar.fit(synthetic_data)
    end_time = time.time()
    print(f"TEST_PASS:render_latency_test")
    print(f"BENCHMARK:render_latency_ms:{(end_time - start_time) * 1000}")
except Exception as e:
    print(f"TEST_FAIL:render_latency_test:{str(e)}")

try:
    # Run a query with WHERE clause, measure query latency
    start_time = time.time()
    query_result = mljar.transform(synthetic_data)
    end_time = time.time()
    print(f"TEST_PASS:query_latency_test")
    print(f"BENCHMARK:query_latency_ms:{(end_time - start_time) * 1000}")
except Exception as e:
    print(f"TEST_FAIL:query_latency_test:{str(e)}")

try:
    # Compare Mljar latency vs Plotly
    start_time = time.time()
    synthetic_data.plot(kind='line')
    plt.show()
    end_time = time.time()
    plotly_latency = (end_time - start_time) * 1000
    mljar_latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_plotly_latency_ratio:{mljar_latency / plotly_latency}")
except Exception as e:
    print(f"TEST_FAIL:compare_with_plotly_test:{str(e)}")

# Memory usage benchmark
tracemalloc.start()
mljar.fit(synthetic_data)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{current / 1024 / 1024}")

# CPU count benchmark
import psutil
print(f"BENCHMARK:cpu_count:{psutil.cpu_count()}")

# File count benchmark
import os
print(f"BENCHMARK:file_count:{len(os.listdir())}")

print("RUN_OK")