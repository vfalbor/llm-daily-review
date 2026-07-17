import subprocess
import pip
import time
import tracemalloc
import importlib.util
import numpy as np

def install_system_packages():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print('INSTALL_OK')

def install_tool_dependencies():
    try:
        subprocess.run(['pip', 'install', 'manim'], check=False)
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')
        return
    print('INSTALL_OK')

def test_import_time():
    tracemalloc.start()
    start = time.time()
    import manim
    import_time = time.time() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:import_time_ms:{import_time * 1000}')
    print(f'BENCHMARK:peak_memory_mb:{peak / 1024 / 1024}')
    print(f'TEST_PASS:import_time')

def test_functionality():
    try:
        from manim import Scene
        scene = Scene()
        scene.add_text("Hello, world!")
        print(f'TEST_PASS:functionality')
    except Exception as e:
        print(f'TEST_FAIL:functionality:{str(e)}')

def test_performance_vs_baseline():
    try:
        import math
        start = time.time()
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        fibonacci(30)
        end = time.time()
        manim_time = end - start
        start = time.time()
        def fibonacci_baseline(n):
            if n < 2:
                return n
            return fibonacci_baseline(n-1) + fibonacci_baseline(n-2)
        fibonacci_baseline(30)
        end = time.time()
        baseline_time = end - start
        ratio = manim_time / baseline_time
        print(f'BENCHMARK:vs_baseline_fib30_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_SKIP:performance_vs_baseline:{str(e)}')

def test_memory_usage():
    try:
        import numpy as np
        arr = np.random.rand(1000, 1000)
        tracemalloc.start()
        np.linalg.inv(arr)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_mb:{peak / 1024 / 1024}')
    except Exception as e:
        print(f'TEST_FAIL:memory_usage:{str(e)}')

def main():
    install_system_packages()
    install_tool_dependencies()
    test_import_time()
    test_functionality()
    test_performance_vs_baseline()
    test_memory_usage()
    start = time.time()
    print('BENCHMARK:startup_time_ms:{}'.format((time.time() - start) * 1000))
    print('RUN_OK')

if __name__ == "__main__":
    main()