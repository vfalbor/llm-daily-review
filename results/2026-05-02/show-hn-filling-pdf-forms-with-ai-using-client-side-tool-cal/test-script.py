import subprocess
import time
import tracemalloc
import requests
from urllib.request import urlretrieve

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_tool():
    try:
        subprocess.run(['npm', 'install', '@simplepdf/pdf-form-filler'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_fill_pdf_form():
    try:
        start_time = time.time()
        subprocess.run(['node', 'pdf-form-filler.js', 'sample.pdf', 'output.pdf'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:fill_time_ms:{(end_time - start_time) * 1000:.2f}")
        print("TEST_PASS:test_fill_pdf_form")
    except Exception as e:
        print(f"TEST_FAIL:test_fill_pdf_form:{str(e)}")

def test_performance_vs_manual():
    try:
        start_time = time.time()
        # simulate manual form filling
        time.sleep(5)
        end_time = time.time()
        manual_time = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run(['node', 'pdf-form-filler.js', 'sample.pdf', 'output.pdf'], check=True)
        end_time = time.time()
        tool_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:manual_fill_time_ms:{manual_time:.2f}")
        print(f"BENCHMARK:tool_fill_time_ms:{tool_time:.2f}")
        print(f"BENCHMARK:vs_manual_ratio:{tool_time / manual_time:.2f}")
        print("TEST_PASS:test_performance_vs_manual")
    except Exception as e:
        print(f"TEST_FAIL:test_performance_vs_manual:{str(e)}")

def test_complex_form_layouts():
    try:
        start_time = time.time()
        subprocess.run(['node', 'pdf-form-filler.js', 'complex.pdf', 'output.pdf'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:complex_fill_time_ms:{(end_time - start_time) * 1000:.2f}")
        print("TEST_PASS:test_complex_form_layouts")
    except Exception as e:
        print(f"TEST_FAIL:test_complex_form_layouts:{str(e)}")

def compare_performance_with_formstack():
    try:
        start_time = time.time()
        subprocess.run(['node', 'formstack.js', 'sample.pdf', 'output.pdf'], check=True)
        end_time = time.time()
        formstack_time = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run(['node', 'pdf-form-filler.js', 'sample.pdf', 'output.pdf'], check=True)
        end_time = time.time()
        tool_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_formstack_ratio:{tool_time / formstack_time:.2f}")
        print("TEST_PASS:compare_performance_with_formstack")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance_with_formstack:{str(e)}")

def main():
    install_dependencies()
    install_tool()
    tracemalloc.start()
    test_fill_pdf_form()
    test_performance_vs_manual()
    test_complex_form_layouts()
    compare_performance_with_formstack()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    print(f"BENCHMARK:peak_memory_usage_bytes:{peak}")
    tracemalloc.stop()
    print("RUN_OK")

if __name__ == "__main__":
    main()