import subprocess
import importlib
import time
import tracemalloc
import sys

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    try:
        subprocess.run(['pip', 'install', 'claude-code-routines'], check=True)
    except subprocess.CalledProcessError:
        subprocess.run(['git', 'clone', 'https://github.com/claude/claude-code-routines.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './claude-code-routines'], cwd='./claude-code-routines', check=True)

def test_install_and_run():
    try:
        import claude_code_routines
        print("INSTALL_OK")
        try:
            claude_code_routines.main()
            print("TEST_PASS:claude_code_routines")
        except Exception as e:
            print(f"TEST_FAIL:claude_code_routines:{str(e)}")
    except ImportError:
        print("INSTALL_FAIL:claude_code_routines could not be imported")

def test_performance():
    import claude_code_routines
    import time
    start_time = time.time()
    claude_code_routines.main()
    end_time = time.time()
    print(f"BENCHMARK:claude_code_routines_latency_ms:{(end_time - start_time) * 1000}")
    tracemalloc.start()
    claude_code_routines.main()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:claude_code_routines_memory_mb:{peak / 10**6}")
    tracemalloc.stop()

def test_vs_baseline():
    import timeit
    import fib
    claude_time = timeit.timeit(lambda: importlib.import_module('claude_code_routines'), number=100)
    fib_time = timeit.timeit(lambda: importlib.import_module('fib'), number=100)
    print(f"BENCHMARK:vs_fib_import_time_ratio:{claude_time / fib_time}")

def main():
    install_dependencies()
    test_install_and_run()
    test_performance()
    test_vs_baseline()
    print("RUN_OK")

if __name__ == "__main__":
    main()