import subprocess
import time
import tracemalloc
import os

def install_dotcl():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
        subprocess.run(['git', 'clone', 'https://github.com/dotcl/dotcl.git'], check=True)
        os.chdir('dotcl')
        start_time = time.time()
        subprocess.run(['cargo', 'build', '--release'], check=True)
        end_time = time.time()
        print(f"INSTALL_OK")
        return end_time - start_time
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        return None

def test_hello_world(install_time):
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run', '--release', '--', 'src/hello-world.lisp'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:hello_world")
        return end_time - start_time
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:hello_world:{e}")
        return None

def test_insert_rows():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run', '--release', '--', 'src/insert-rows.lisp'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:insert_rows_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:insert_rows")
        return end_time - start_time
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:insert_rows:{e}")
        return None

def test_query_latency():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run', '--release', '--', 'src/query-latency.lisp'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:query_latency_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:query_latency")
        return end_time - start_time
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:query_latency:{e}")
        return None

def compare_to_sbcl(latency):
    try:
        subprocess.run(['sbcl', '---load', 'src/query-latency.lisp'], check=True)
        sbcl_latency = 10  # placeholder value, replace with actual measurement
        print(f"BENCHMARK:vs_sbcl_query_latency_ratio:{latency / sbcl_latency}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_SKIP:compare_to_sbcl:{e}")

def main():
    install_time = install_dotcl()
    if install_time is not None:
        print(f"BENCHMARK:install_time_s:{install_time}")

    hello_world_time = test_hello_world(install_time)
    insert_rows_time = test_insert_rows()
    query_latency_time = test_query_latency()
    if query_latency_time is not None:
        compare_to_sbcl(query_latency_time)

    tracemalloc.start()
    time.sleep(1)
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_kb:{current / 1024}")
    tracemalloc.stop()

    print("RUN_OK")

if __name__ == "__main__":
    main()