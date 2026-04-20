import subprocess
import time
import tracemalloc
import sqlite3
import os
import xata

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'sqlite'], check=False)
        subprocess.run(['pip', 'install', 'xata'], check=False)
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def create_database():
    try:
        xata.api_key = "mock_api_key"
        db = xata.Database()
        return db
    except Exception as e:
        print(f"TEST_FAIL:create_database:{str(e)}")
        return None

def create_schema(db):
    try:
        db.create_schema({"name": "string", "age": "int"})
        print("TEST_PASS:create_schema")
    except Exception as e:
        print(f"TEST_FAIL:create_schema:{str(e)}")

def perform_write_operation(db):
    try:
        for i in range(1000):
            db.insert({"name": f"Name {i}", "age": i})
        print("TEST_PASS:perform_write_operation")
    except Exception as e:
        print(f"TEST_FAIL:perform_write_operation:{str(e)}")

def query_database(db):
    try:
        start_time = time.time()
        results = db.query({"age": 500})
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:query_latency_ms:{latency}")
    except Exception as e:
        print(f"TEST_FAIL:query_database:{str(e)}")

def compare_to_baseline():
    try:
        # Create an in-memory SQLite database
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
        c.execute("CREATE TABLE users (name text, age int)")
        for i in range(1000):
            c.execute("INSERT INTO users VALUES (?, ?)", (f"Name {i}", i))
        conn.commit()
        start_time = time.time()
        c.execute("SELECT * FROM users WHERE age = 500")
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:sqlite_query_latency_ms:{latency}")
        try:
            db = create_database()
            query_database(db)
            print(f"BENCHMARK:vs_sqlite_query_latency_ratio:{(latency / (time.time() - start_time) * 1000)}")
        except Exception as e:
            print(f"TEST_FAIL:compare_to_baseline:{str(e)}")
    except Exception as e:
        print(f"TEST_FAIL:compare_to_baseline:{str(e)}")

def benchmark_memory():
    try:
        tracemalloc.start()
        db = create_database()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_bytes:{current}")
    except Exception as e:
        print(f"TEST_FAIL:benchmark_memory:{str(e)}")

def benchmark_import_time():
    try:
        start_time = time.time()
        import xata
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time}")
    except Exception as e:
        print(f"TEST_FAIL:benchmark_import_time:{str(e)}")

def main():
    install_dependencies()
    db = create_database()
    if db is not None:
        create_schema(db)
        perform_write_operation(db)
        query_database(db)
    compare_to_baseline()
    benchmark_memory()
    benchmark_import_time()
    print("RUN_OK")

if __name__ == "__main__":
    main()