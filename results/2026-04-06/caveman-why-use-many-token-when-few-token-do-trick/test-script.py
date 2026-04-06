import importlib
import importlib.util
import time
import sys
import os
import random
import string

def install_package(package_name):
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {e}")

def test_few_token():
    try:
        import caveman
        few_token_result = caveman.generate_text(prompt="Hello", max_tokens=5)
        many_token_result = caveman.generate_text(prompt="Hello", max_tokens=50)
        if len(few_token_result) > len(many_token_result):
            print(f"TEST_PASS:few_token_test")
        else:
            print(f"TEST_FAIL:few_token_test:Many tokens did not produce more output than few tokens")
    except Exception as e:
        print(f"TEST_FAIL:few_token_test:{e}")

def run_multiple_tests():
    try:
        import caveman
        results = []
        for _ in range(10):
            prompt = ''.join(random.choices(string.ascii_lowercase, k=10))
            few_token_result = caveman.generate_text(prompt=prompt, max_tokens=5)
            many_token_result = caveman.generate_text(prompt=prompt, max_tokens=50)
            results.append((few_token_result, many_token_result))
        few_token_length = sum(len(result[0]) for result in results)
        many_token_length = sum(len(result[1]) for result in results)
        if few_token_length < many_token_length:
            print(f"TEST_PASS:multiple_tests")
        else:
            print(f"TEST_FAIL:multiple_tests:Few tokens produced more output than many tokens")
        print(f"BENCHMARK:average_few_token_length:{few_token_length / len(results)}")
        print(f"BENCHMARK:average_many_token_length:{many_token_length / len(results)}")
    except Exception as e:
        print(f"TEST_FAIL:multiple_tests:{e}")

def benchmark_import_time():
    try:
        import time
        start_time = time.time()
        importlib.import_module("caveman")
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time}")
    except Exception as e:
        print(f"TEST_FAIL:benchmark_import_time:{e}")

def main():
    install_package("caveman")
    start_time = time.time()
    test_few_token()
    run_multiple_tests()
    benchmark_import_time()
    end_time = time.time()
    print(f"BENCHMARK:total_test_time_ms:{(end_time - start_time) * 1000}")
    print("RUN_OK")

if __name__ == "__main__":
    main()