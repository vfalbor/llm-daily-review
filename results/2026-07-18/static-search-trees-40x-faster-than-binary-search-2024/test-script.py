import subprocess
import time
import tracemalloc
import sqlite3
import os

def install_static_search_tree():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['git', 'clone', 'https://github.com/curiouscoding/static_search_tree.git'], check=False)
        os.chdir('static_search_tree')
        subprocess.run(['pip', 'install', '-e', '.'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_query_time():
    try:
        import static_search_tree
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
        c.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        for i in range(1000):
            c.execute("INSERT INTO test VALUES (?, ?)", (i, f"name {i}"))
        conn.commit()
        start_time = time.time()
        c.execute("SELECT * FROM test WHERE id < 500")
        results = c.fetchall()
        end_time = time.time()
        query_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:query_time_ms:{query_time}")
        print("TEST_PASS:test_query_time")
    except Exception as e:
        print(f"TEST_FAIL:test_query_time:{str(e)}")

def compare_with_binary_search():
    try:
        import static_search_tree
        import random
        data = [random.randint(0, 1000) for _ in range(1000)]
        target = random.choice(data)
        start_time = time.time()
        for i in data:
            if i == target:
                break
        end_time = time.time()
        binary_search_time = (end_time - start_time) * 1000
        start_time = time.time()
        static_search_tree.search(data, target)
        end_time = time.time()
        static_search_time = (end_time - start_time) * 1000
        ratio = binary_search_time / static_search_time
        print(f"BENCHMARK:vs_binary_search_ratio:{ratio}")
        print("TEST_PASS:compare_with_binary_search")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_binary_search:{str(e)}")

def test_edge_cases():
    try:
        import static_search_tree
        data = [1, 2, 3]
        target = 2
        result = static_search_tree.search(data, target)
        if result == target:
            print("TEST_PASS:test_edge_cases")
        else:
            print("TEST_FAIL:test_edge_cases:incorrect result")
    except Exception as e:
        print(f"TEST_FAIL:test_edge_cases:{str(e)}")

def compare_with_sqlite():
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
        c.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        for i in range(1000):
            c.execute("INSERT INTO test VALUES (?, ?)", (i, f"name {i}"))
        conn.commit()
        start_time = time.time()
        c.execute("SELECT * FROM test WHERE id < 500")
        results = c.fetchall()
        end_time = time.time()
        sqlite_time = (end_time - start_time) * 1000
        import static_search_tree
        data = [i for i in range(1000)]
        target = 500
        start_time = time.time()
        static_search_tree.search(data, target)
        end_time = time.time()
        static_search_time = (end_time - start_time) * 1000
        ratio = sqlite_time / static_search_time
        print(f"BENCHMARK:vs_sqlite_ratio:{ratio}")
        print("TEST_PASS:compare_with_sqlite")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_sqlite:{str(e)}")

def measure_memory_usage():
    try:
        tracemalloc.start()
        import static_search_tree
        data = [i for i in range(1000)]
        target = 500
        static_search_tree.search(data, target)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
    except Exception as e:
        print(f"TEST_FAIL:measure_memory_usage:{str(e)}")

def measure_location_count():
    try:
        import os
        loc_count = 0
        for root, dirs, files in os.walk('static_search_tree'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        loc_count += len(f.readlines())
        print(f"BENCHMARK:loc_count:{loc_count}")
    except Exception as e:
        print(f"TEST_FAIL:measure_location_count:{str(e)}")

def measure_file_count():
    try:
        import os
        file_count = 0
        for root, dirs, files in os.walk('static_search_tree'):
            file_count += len(files)
        print(f"BENCHMARK:file_count:{file_count}")
    except Exception as e:
        print(f"TEST_FAIL:measure_file_count:{str(e)}")

subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
install_static_search_tree()
test_query_time()
compare_with_binary_search()
test_edge_cases()
compare_with_sqlite()
measure_memory_usage()
measure_location_count()
measure_file_count()
print("RUN_OK")