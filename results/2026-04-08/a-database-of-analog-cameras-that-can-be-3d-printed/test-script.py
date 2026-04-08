import subprocess
import time
import tracemalloc
import sqlite3
import random

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'sqlite3'], check=True)
except subprocess.CalledProcessError:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/ghaering/pysqlite3.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './pysqlite3'], check=True)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL: Unable to install sqlite3")
        exit(1)

print("INSTALL_OK")

# Create an in-memory DB and insert 1000 rows
import sqlite3
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute('CREATE TABLE cameras (model TEXT, year INTEGER)')
for i in range(1000):
    cursor.execute('INSERT INTO cameras VALUES (?, ?)', (f"Camera {i}", random.randint(1900, 2022)))
conn.commit()

# Measure latency vs sqlite3 stdlib as baseline
tracemalloc.start()
start_time = time.time()
for _ in range(100):
    cursor.execute('SELECT * FROM cameras WHERE year > 2000')
end_time = time.time()
cur_time, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:query_latency_ms:{(end_time - start_time) * 1000 / 100:.2f}")
print(f"BENCHMARK:memory_usage_bytes:{cur_time}")

# Search for a specific camera model and report any issues
try:
    start_time = time.time()
    cursor.execute('SELECT * FROM cameras WHERE model = "Camera 500"')
    result = cursor.fetchone()
    if result is None:
        print("TEST_FAIL:search_camera:Camera not found")
    else:
        print(f"TEST_PASS:search_camera")
    end_time = time.time()
    tracemalloc.start()
    for _ in range(100):
        cursor.execute('SELECT * FROM cameras WHERE model = "Camera 500"')
    tracemalloc.stop()
    cur_time, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:search_camera_latency_ms:{(end_time - start_time) * 1000 / 100:.2f}")
    print(f"BENCHMARK:search_camera_memory_usage_bytes:{cur_time}")
except Exception as e:
    print(f"TEST_FAIL:search_camera:{str(e)}")

# Compare performance vs sqlite3 stdlib as baseline
import sqlite3
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute('CREATE TABLE cameras (model TEXT, year INTEGER)')
for i in range(1000):
    cursor.execute('INSERT INTO cameras VALUES (?, ?)', (f"Camera {i}", random.randint(1900, 2022)))
conn.commit()
tracemalloc.start()
start_time = time.time()
for _ in range(100):
    cursor.execute('SELECT * FROM cameras WHERE year > 2000')
end_time = time.time()
cur_time, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
baseline_time = (end_time - start_time) * 1000 / 100
baseline_memory = cur_time
print(f"BENCHMARK:vs_sqlite_query_latency_ms:{baseline_time:.2f}")
print(f"BENCHMARK:vs_sqlite_memory_usage_bytes:{baseline_memory}")

print("RUN_OK")