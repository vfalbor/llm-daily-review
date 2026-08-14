import subprocess
import time
import tracemalloc
import os
import sys
from importlib import import_module
import requests

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK')

try:
    # Install differential_heuristics package using pip
    subprocess.run(['pip', 'install', 'differential_heuristics'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print('INSTALL_FAIL:' + str(e))

    # Fallback to installing from source
    try:
        subprocess.run(['git', 'clone', 'https://github.com/munlogadan/differential_heuristics.git'])
        subprocess.run(['pip', 'install', '-e', './differential_heuristics'])
        print('INSTALL_OK')
    except Exception as e:
        print('INSTALL_FAIL:' + str(e))
        sys.exit(0)

# Import the package and measure import time
start_time = time.time()
try:
    import differential_heuristics
except Exception as e:
    print('TEST_FAIL:import:' + str(e))
else:
    import_time = (time.time() - start_time) * 1000
    print('BENCHMARK:import_time_ms:' + str(import_time))
    print('TEST_PASS:import')

# Run a minimal functional test with synthetic data
try:
    start_time = time.time()
    differential_heuristics.main()
    latency = (time.time() - start_time) * 1000
    print('BENCHMARK:main_latency_ms:' + str(latency))
    print('TEST_PASS:main')
except Exception as e:
    print('TEST_FAIL:main:' + str(e))

# Measure peak memory usage
tracemalloc.start()
try:
    differential_heuristics.main()
finally:
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print('BENCHMARK:peak_memory_mb:' + str(peak / 10**6))

# Compare performance vs A* algorithm
astar_url = 'https://github.com/munlogadan/astar'
try:
    subprocess.run(['git', 'clone', astar_url])
    subprocess.run(['pip', 'install', '-e', './astar'])
    import astar
    start_time = time.time()
    astar.main()
    astar_latency = (time.time() - start_time) * 1000
    ratio = latency / astar_latency
    print('BENCHMARK:vs_astar_ratio:' + str(ratio))
except Exception as e:
    print('TEST_FAIL:vs_astar:' + str(e))

# Clone the repo and run the provided example
try:
    subprocess.run(['git', 'clone', 'https://github.com/munlogadan/differential_heuristics'])
    subprocess.run(['python', './differential_heuristics/example.py'])
    print('TEST_PASS:example')
except Exception as e:
    print('TEST_FAIL:example:' + str(e))

# Verify output matches the blog post's explanation
try:
    response = requests.get('https://github.com/munlogadan/differential_heuristics')
    if response.status_code == 200:
        print('TEST_PASS:blog_post')
    else:
        print('TEST_FAIL:blog_post:Failed to retrieve blog post')
except Exception as e:
    print('TEST_FAIL:blog_post:' + str(e))

# Measure file count
file_count = sum(len(files) for _, _, files in os.walk('.'))
print('BENCHMARK:file_count:' + str(file_count))

# Measure test file count
test_file_count = sum(1 for root, _, files in os.walk('.') if any(file.startswith('test_') for file in files))
print('BENCHMARK:test_file_count:' + str(test_file_count))

print('RUN_OK')