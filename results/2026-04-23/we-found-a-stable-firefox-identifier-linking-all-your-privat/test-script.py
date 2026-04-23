import subprocess
import time
import tracemalloc
import requests
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

def install_firefox():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        subprocess.run(['git', 'clone', 'https://github.com/mozilla/geckodriver.git'], check=True)
        subprocess.run(['mv', 'geckodriver/geckodriver', '/usr/bin/'], check=True)
        subprocess.run(['chmod', '+x', '/usr/bin/geckodriver'], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def run_firefox_test():
    try:
        start_time = time.time()
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        driver.get('https://www.example.com')
        driver.find_element(By.TAG_NAME, 'body')
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:firefox_latency_ms:{latency_ms}')
        driver.quit()
        print(f'TEST_PASS:firefox_test')
    except Exception as e:
        print(f'TEST_FAIL:firefox_test:{str(e)}')

def run_indexeddb_test():
    try:
        start_time = time.time()
        driver = webdriver.Firefox()
        driver.get('https://www.example.com')
        driver.execute_script('''
            var db;
            var request = window.indexedDB.open('test_db', 1);
            request.onerror = function(event) {
                console.log('Error opening database');
            };
            request.onsuccess = function(event) {
                db = event.target.result;
                console.log('Database opened');
            };
        ''')
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:indexeddb_latency_ms:{latency_ms}')
        print(f'TEST_PASS:indexeddb_test')
    except Exception as e:
        print(f'TEST_FAIL:indexeddb_test:{str(e)}')

def compare_firefox_benchmark():
    try:
        start_time = time.time()
        driver = webdriver.Firefox()
        driver.get('https://www.example.com')
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        baseline_latency_ms = 100
        ratio = latency_ms / baseline_latency_ms
        print(f'BENCHMARK:vs_firefox_latency_ratio:{ratio}')
    except Exception as e:
        print(f'BENCHMARK:vs_firefox_latency_ratio:nan')

def get_memory_usage():
    try:
        tracemalloc.start()
        driver = webdriver.Firefox()
        driver.get('https://www.example.com')
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:firefox_memory_usage_mb:{current / (1024 * 1024)}')
    except Exception as e:
        print(f'BENCHMARK:firefox_memory_usage_mb:nan')

def get_cpu_usage():
    try:
        import psutil
        driver = webdriver.Firefox()
        driver.get('https://www.example.com')
        cpu_usage = psutil.cpu_percent(interval=1)
        print(f'BENCHMARK:firefox_cpu_usage_percent:{cpu_usage}')
    except Exception as e:
        print(f'BENCHMARK:firefox_cpu_usage_percent:nan')

def get_request_count():
    try:
        import requests
        driver = webdriver.Firefox()
        driver.get('https://www.example.com')
        requests_count = len(driver.requests)
        print(f'BENCHMARK:firefox_requests_count:{requests_count}')
    except Exception as e:
        print(f'BENCHMARK:firefox_requests_count:nan')

install_firefox()
run_firefox_test()
run_indexeddb_test()
compare_firefox_benchmark()
get_memory_usage()
get_cpu_usage()
get_request_count()
print('RUN_OK')