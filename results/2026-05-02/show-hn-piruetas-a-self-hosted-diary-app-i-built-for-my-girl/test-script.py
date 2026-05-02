import subprocess
import requests
import time
import tracemalloc
import os
import sys

def install_piruetas():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=True)
        subprocess.run(['npm', 'install', '-g', '@piruetas/cli'], check=True)
        return True
    except Exception as e:
        print(f"INSTALL_FAIL:Failed to install Piruetas: {str(e)}")
        return False

def test_create_diary_entry():
    try:
        subprocess.run(['piruetas', 'init', 'test-diary'], check=True)
        subprocess.run(['piruetas', 'new', 'Test Entry'], check=True)
        print("TEST_PASS:test_create_diary_entry")
    except Exception as e:
        print(f"TEST_FAIL:test_create_diary_entry:{str(e)}")

def test_insert_10_diary_entries():
    try:
        start_time = time.time()
        for i in range(10):
            subprocess.run(['piruetas', 'new', f'Test Entry {i}'], check=True)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:insert_latency_ms:{latency:.2f}")
        print("TEST_PASS:test_insert_10_diary_entries")
    except Exception as e:
        print(f"TEST_FAIL:test_insert_10_diary_entries:{str(e)}")

def test_query_latency():
    try:
        start_time = time.time()
        subprocess.run(['piruetas', 'search', 'test'], check=True)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:query_latency_ms:{latency:.2f}")
        print("TEST_PASS:test_query_latency")
    except Exception as e:
        print(f"TEST_FAIL:test_query_latency:{str(e)}")

def test_compare_piruetas_jekyll_latency():
    try:
        # Install Jekyll
        subprocess.run(['apk', 'add', '--no-cache', 'ruby', 'ruby-dev', 'build-base'], check=True)
        subprocess.run(['gem', 'install', 'jekyll'], check=True)
        # Create a Jekyll site
        subprocess.run(['jekyll', 'new', 'test-jekyll'], check=True)
        # Start Jekyll server
        jekyll_server = subprocess.Popen(['jekyll', 'serve'], cwd='test-jekyll')
        time.sleep(5)  # Wait for server to start
        # Measure Jekyll latency
        start_time = time.time()
        requests.get('http://localhost:4000')
        end_time = time.time()
        jekyll_latency = (end_time - start_time) * 1000
        # Measure Piruetas latency
        start_time = time.time()
        subprocess.run(['piruetas', 'serve'], check=True)
        time.sleep(5)  # Wait for server to start
        requests.get('http://localhost:8080')
        end_time = time.time()
        piruetas_latency = (end_time - start_time) * 1000
        # Compare latencies
        ratio = piruetas_latency / jekyll_latency
        print(f"BENCHMARK:vs_jekyll_latency_ratio:{ratio:.2f}")
        print("TEST_PASS:test_compare_piruetas_jekyll_latency")
    except Exception as e:
        print(f"TEST_FAIL:test_compare_piruetas_jekyll_latency:{str(e)}")

def main():
    print("INSTALL_OK")
    if not install_piruetas():
        return
    test_create_diary_entry()
    test_insert_10_diary_entries()
    test_query_latency()
    test_compare_piruetas_jekyll_latency()
    # Additional benchmarks
    tracemalloc.start()
    time.sleep(1)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_kb:{current / 1024:.2f}")
    print(f"BENCHMARK:peak_memory_usage_kb:{peak / 1024:.2f}")
    print("RUN_OK")

if __name__ == '__main__':
    main()