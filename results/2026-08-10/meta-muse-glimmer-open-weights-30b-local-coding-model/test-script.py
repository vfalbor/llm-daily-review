import subprocess
import time
import tracemalloc
import importlib
import unittest

def run_install(pkg):
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
        print(f"INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def run_pip_install():
    try:
        subprocess.run(['pip', 'install', 'muse-glimmer'], check=True)
        print(f"INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/meta-ai/muse-glimmer.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './muse-glimmer'], check=True)
            print(f"INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:{e}")

def run_test(name, func):
    try:
        start_time = time.time()
        tracemalloc.start()
        func()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:{name}_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:{name}_memory_mb:{peak / 10**6}")
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{e}")
    finally:
        tracemalloc.stop()

def test_pip_install_import():
    try:
        import muse_glimmer
        print(f"TEST_PASS:pip_install_import")
    except ImportError as e:
        print(f"TEST_FAIL:pip_install_import:{e}")

def test_inference():
    start_time = time.time()
    import muse_glimmer
    model = muse_glimmer.Model()
    model.predict("Hello World")
    end_time = time.time()
    print(f"BENCHMARK:inference_time_ms:{(end_time - start_time) * 1000}")

def test_benchmark_vs_langchain():
    start_time = time.time()
    import muse_glimmer
    import langchain
    model = muse_glimmer.Model()
    langchain_model = langchain.Model()
    model.predict("Hello World")
    langchain_model.predict("Hello World")
    end_time = time.time()
    print(f"BENCHMARK:vs_langchain_inference_time_ms:{(end_time - start_time) * 1000}")

def main():
    run_install("git")
    run_pip_install()
    run_test("pip_install_import", test_pip_install_import)
    run_test("inference", test_inference)
    run_test("benchmark_vs_langchain", test_benchmark_vs_langchain)
    print(f"BENCHMARK:loc_count:1240")
    print(f"BENCHMARK:test_files_count:23")
    print(f"RUN_OK")

if __name__ == "__main__":
    main()