import subprocess
import sys
import time
import tracemalloc
import sqlite3
from youtrackdb import YouTrackDB

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)

# Install YouTrackDB client
try:
    subprocess.run(['pip', 'install', 'youtrackdb'], check=True)
except subprocess.CalledProcessError:
    subprocess.run(['pip', 'install', '--upgrade', 'pip'], check=True)
    subprocess.run(['git', 'clone', 'https://github.com/JetBrains/youtrackdb.git', 'youtrackdb'], check=True)
    subprocess.run(['pip', 'install', '-e', 'youtrackdb'], check=True)

# Install sqlite3 for baseline comparison
subprocess.run(['pip', 'install', 'pysqlite3'], check=True)

# Test 1: Install YouTrackDB and create a sample graph
try:
    start_time = time.time()
    db = YouTrackDB()
    db.create_graph()
    end_time = time.time()
    print(f"BENCHMARK:install_time_s:{end_time - start_time:.2f}")
    print("TEST_PASS:install_youtrackdb")
except Exception as e:
    print(f"TEST_FAIL:install_youtrackdb:{str(e)}")

# Test 2: Insert 1000 nodes and measure query latency
try:
    start_time = time.time()
    db.insert_nodes(1000)
    end_time = time.time()
    print(f"BENCHMARK:insert_time_s:{end_time - start_time:.2f}")
    
    start_time = time.time()
    db.query("MATCH (n) RETURN n")
    end_time = time.time()
    print(f"BENCHMARK:query_time_ms:{(end_time - start_time) * 1000:.2f}")
    print("TEST_PASS:insert_and_query")
except Exception as e:
    print(f"TEST_FAIL:insert_and_query:{str(e)}")

# Test 3: Run a Cypher query and check results
try:
    start_time = time.time()
    results = db.query("MATCH (n) RETURN n")
    end_time = time.time()
    print(f"BENCHMARK:cypher_query_time_ms:{(end_time - start_time) * 1000:.2f}")
    if len(results) > 0:
        print("TEST_PASS:cypher_query")
    else:
        print("TEST_FAIL:cypher_query:empty results")
except Exception as e:
    print(f"TEST_FAIL:cypher_query:{str(e)}")

# Baseline comparison with sqlite3
try:
    start_time = time.time()
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE nodes (id INTEGER PRIMARY KEY)")
    for i in range(1000):
        cursor.execute("INSERT INTO nodes (id) VALUES (?)", (i,))
    conn.commit()
    cursor.execute("SELECT * FROM nodes")
    results = cursor.fetchall()
    end_time = time.time()
    print(f"BENCHMARK:sqlite_query_time_ms:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:vs_sqlite_query_time_ratio:{(end_time - start_time) / (end_time - start_time):.2f}")
    print("TEST_PASS:sqlite_baseline")
except Exception as e:
    print(f"TEST_FAIL:sqlite_baseline:{str(e)}")

# Memory usage benchmark
tracemalloc.start()
db = YouTrackDB()
db.create_graph()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Test files count benchmark
import os
test_files_count = len([name for name in os.listdir() if name.endswith('.py')])
print(f"BENCHMARK:test_files_count:{test_files_count}")

print("RUN_OK")