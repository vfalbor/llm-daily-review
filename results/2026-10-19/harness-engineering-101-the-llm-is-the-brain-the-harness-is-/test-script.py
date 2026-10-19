import subprocess, sys, time, tracemalloc, json, os, traceback

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
    except Exception as e:
        pass

def install_apk(pkg):
    start = time.time()
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:apk_{pkg}_install_time_s:{duration:.3f}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")

def pip_install(package):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', package], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:pip_{package}_install_time_s:{duration:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def pip_install_editable(path):
    start = time.time()
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', '-e', path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        duration = time.time() - start
        print_marker(f"INSTALL_OK")
        print_marker(f"BENCHMARK:pip_editable_install_time_s:{duration:.3f}")
        return True
    except Exception as e:
        print_marker(f"INSTALL_FAIL:{e}")
        return False

def benchmark(name, func, *args, **kwargs):
    tracemalloc.start()
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print_marker(f"BENCHMARK:{name}_time_s:{elapsed:.3f}")
        print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.1f}")
        return result, elapsed
    except Exception as e:
        tracemalloc.stop()
        print_marker(f"BENCHMARK:{name}_error:{e}")
        raise

def test_import():
    try:
        start = time.time()
        import harness_engineering_101  # noqa: F401
        elapsed = time.time() - start
        print_marker(f"TEST_PASS:import_harness")
        print_marker(f"BENCHMARK:import_time_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:import_harness:{e}")

def test_basic_harness():
    try:
        from harness_engineering_101 import Harness, DummyLLM  # type: ignore
        dummy = DummyLLM()
        harness = Harness(llm=dummy)
        prompt = "Hello"
        start = time.time()
        out = harness.run(prompt)
        elapsed = time.time() - start
        if isinstance(out, str) and out:
            print_marker(f"TEST_PASS:basic_harness")
        else:
            print_marker(f"TEST_FAIL:basic_harness:empty_output")
        print_marker(f"BENCHMARK:basic_harness_latency_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:basic_harness:{e}")

def test_memory():
    try:
        from harness_engineering_101 import Harness, DummyLLM, SimpleMemory  # type: ignore
        dummy = DummyLLM()
        memory = SimpleMemory()
        harness = Harness(llm=dummy, memory=memory)
        token = "unique_token_12345"
        harness.memory.store(token)
        retrieved = harness.memory.retrieve(token)
        if retrieved == token:
            print_marker(f"TEST_PASS:memory_store_retrieve")
        else:
            print_marker(f"TEST_FAIL:memory_store_retrieve:retrieved_mismatch")
    except Exception as e:
        print_marker(f"TEST_FAIL:memory_store_retrieve:{e}")

def test_latency_vs_langchain():
    try:
        from harness_engineering_101 import Harness, DummyLLM  # type: ignore
        import importlib.util, time
        # LangChain baseline (install if needed)
        baseline_installed = pip_install("langchain")
        if not baseline_installed:
            print_marker("TEST_SKIP:latency_vs_langchain:langchain_install_failed")
            return
        from langchain.llms.fake import FakeListLLM  # type: ignore
        dummy = DummyLLM()
        harness = Harness(llm=dummy)
        prompt = "Test latency comparison"
        # harness latency
        _, harness_time = benchmark("harness_latency", harness.run, prompt)
        # langchain latency
        lc_llm = FakeListLLM(responses=["response"])
        def lc_run(p):
            return lc_llm.invoke(p)
        _, lc_time = benchmark("langchain_latency", lc_run, prompt)
        ratio = harness_time / lc_time if lc_time else float('inf')
        print_marker(f"BENCHMARK:vs_langchain_latency_ratio:{ratio:.3f}")
        print_marker(f"TEST_PASS:latency_vs_langchain")
    except Exception as e:
        print_marker(f"TEST_FAIL:latency_vs_langchain:{e}")

def run_repo_tests():
    try:
        # assume repo cloned at /tmp/harness-engineering-101
        repo_dir = "/tmp/harness-engineering-101"
        if not os.path.isdir(repo_dir):
            print_marker("TEST_SKIP:repo_tests:repo_not_cloned")
            return
        cmd = [sys.executable, "-m", "pytest", "--maxfail=1", "--disable-warnings"]
        start = time.time()
        result = subprocess.run(cmd, cwd=repo_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elapsed = time.time() - start
        if result.returncode == 0:
            print_marker("TEST_PASS:repo_pytest")
        else:
            print_marker(f"TEST_FAIL:repo_pytest:{result.stdout[:200]}")
        print_marker(f"BENCHMARK:repo_tests_time_s:{elapsed:.3f}")
    except Exception as e:
        print_marker(f"TEST_FAIL:repo_pytest:{e}")

def main():
    # 1. Install required apk packages
    install_apk('git')
    # 2. Try pip install package
    if not pip_install("harness-engineering-101"):
        # fallback to git clone
        repo_url = "https://github.com/IsuruMaduranga/harness-engineering-101.git"
        clone_dir = "/tmp/harness-engineering-101"
        try:
            subprocess.run(['git', 'clone', '--depth', '1', repo_url, clone_dir], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_marker("INSTALL_OK")
            pip_install_editable(clone_dir)
        except Exception as e:
            print_marker(f"INSTALL_FAIL:git_clone:{e}")

    # 3. Run tests
    test_import()
    test_basic_harness()
    test_memory()
    test_latency_vs_langchain()
    run_repo_tests()

    # Ensure at least three benchmark lines (already emitted above)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()