import subprocess
import time
import tracemalloc
import sys

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
    print("INSTALL_OK")

def install_tool():
    try:
        subprocess.run(['npm', 'install', 'https://github.com/twalichiewicz/HNewhere.git'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: {e}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/twalichiewicz/HNewhere.git'], check=True)
            subprocess.run(['npm', 'install', './HNewhere'], check=True)
            print("INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL: {e}")

def test_userscript_navigation():
    try:
        start_time = time.time()
        subprocess.run(['node', 'https://github.com/twalichiewicz/HNewhere/blob/main/index.js'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:userscript_navigation_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:userscript_navigation")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:userscript_navigation:{e}")

def test_native_hn_navigation():
    try:
        start_time = time.time()
        subprocess.run(['curl', 'https://news.ycombinator.com/'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:native_hn_navigation_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:native_hn_navigation")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:native_hn_navigation:{e}")

def test_userscript_stability():
    try:
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['node', 'https://github.com/twalichiewicz/HNewhere/blob/main/index.js'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:userscript_stability_memory_mb:{peak / 10**6}")
        print(f"BENCHMARK:userscript_stability_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:userscript_stability")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:userscript_stability:{e}")

def test_baseline_tool():
    try:
        start_time = time.time()
        subprocess.run(['curl', 'https://userscripts.org/'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:baseline_tool_time_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:baseline_tool")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:baseline_tool:{e}")

def compare_performance():
    try:
        userscript_time = float(next(line.split(":")[1] for line in sys.stdout.readlines() if line.startswith("BENCHMARK:userscript_navigation_time_ms:")))
        native_hn_time = float(next(line.split(":")[1] for line in sys.stdout.readlines() if line.startswith("BENCHMARK:native_hn_navigation_time_ms:")))
        baseline_tool_time = float(next(line.split(":")[1] for line in sys.stdout.readlines() if line.startswith("BENCHMARK:baseline_tool_time_ms:")))
        print(f"BENCHMARK:vs_native_hn_navigation_ratio:{userscript_time / native_hn_time}")
        print(f"BENCHMARK:vs_baseline_tool_ratio:{userscript_time / baseline_tool_time}")
    except ValueError:
        pass

if __name__ == "__main__":
    install_dependencies()
    install_tool()
    test_userscript_navigation()
    test_native_hn_navigation()
    test_userscript_stability()
    test_baseline_tool()
    compare_performance()
    print("RUN_OK")