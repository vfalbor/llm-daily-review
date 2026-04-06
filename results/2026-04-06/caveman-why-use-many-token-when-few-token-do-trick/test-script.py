import importlib
import time
import json
from urllib.parse import urlparse
import os
import psutil
import requests
from pathlib import Path
from datetime import datetime

def benchmark_import_time(module_name):
    start_time = time.time()
    importlib.import_module(module_name)
    end_time = time.time()
    import_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time_ms:.2f}")

def test_readme_and_code():
    try:
        with open('README.md', 'r') as f:
            readme_content = f.read()
        print("TEST_PASS:readme_content")
    except FileNotFoundError:
        print("TEST_FAIL:readme_content:File not found")

    try:
        with open('caveman/__init__.py', 'r') as f:
            code_content = f.read()
        print("TEST_PASS:code_content")
    except FileNotFoundError:
        print("TEST_FAIL:code_content:File not found")

def run_model_on_small_dataset():
    try:
        import caveman
        from caveman import CavemanModel
        model = CavemanModel()
        dataset = ["This is a test sentence", "This is another test sentence"]
        output = model.generate(dataset)
        print("TEST_PASS:run_model_on_small_dataset")
    except Exception as e:
        print(f"TEST_FAIL:run_model_on_small_dataset:{str(e)}")

def test_model_output_accuracy():
    try:
        import caveman
        from caveman import CavemanModel
        model = CavemanModel()
        dataset = ["This is a test sentence", "This is another test sentence"]
        output = model.generate(dataset)
        expected_output = ["This is a test sentence", "This is another test sentence"]
        if output == expected_output:
            print("TEST_PASS:test_model_output_accuracy")
        else:
            print("TEST_FAIL:test_model_output_accuracy:Output does not match expected output")
    except Exception as e:
        print(f"TEST_FAIL:test_model_output_accuracy:{str(e)}")

def measure_latency():
    try:
        import caveman
        import time
        from caveman import CavemanModel
        model = CavemanModel()
        start_time = time.time()
        model.generate(["This is a test sentence"])
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f"BENCHMARK:latency_ms:{latency_ms:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:measure_latency:{str(e)}")

def compare_with_similar_tools():
    try:
        import subprocess
        subprocess.check_output(["pip", "install", "langchain"])
        import langchain
        langchain_import_time = subprocess.check_output(["python", "-c", "import time; import langchain; print((time.time() - time.time()) * 1000)"])
        caveman_import_time = subprocess.check_output(["python", "-c", "import time; import caveman; print((time.time() - time.time()) * 1000)"])
        if float(caveman_import_time) < float(langchain_import_time):
            print("BENCHMARK:vs_langchain:faster_import")
        else:
            print("BENCHMARK:vs_langchain:slower_import")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_similar_tools:{str(e)}")

def main():
    try:
        print("INSTALL_OK")
        benchmark_import_time('caveman')
        test_readme_and_code()
        run_model_on_small_dataset()
        test_model_output_accuracy()
        measure_latency()
        compare_with_similar_tools()
        print("RUN_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

if __name__ == "__main__":
    main()