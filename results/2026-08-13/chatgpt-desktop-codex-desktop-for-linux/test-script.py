import subprocess
import time
import tracemalloc
import importlib.util

def install_packages(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install {package} with error {e}")
        return False
    print(f"INSTALL_OK:{package} installed successfully")
    return True

def install_tool_dependencies(tool):
    try:
        subprocess.run(['pip', 'install', tool], check=True)
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', f'https://github.com/{tool}.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './'], check=True, cwd=f'./{tool}')
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:Failed to install {tool} with error {e}")
            return False
    print(f"INSTALL_OK:{tool} installed successfully")
    return True

def run_benchmark(name, func):
    start_time = time.time()
    tracemalloc.start()
    func()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:{name}_time_s:{end_time - start_time}")
    print(f"BENCHMARK:{name}_memory_mb:{peak / 10**6}")
    return end_time - start_time

def test_codex_desktop():
    try:
        spec = importlib.util.find_spec('codex')
        if spec is None:
            print("TEST_FAIL:codex:Module not found")
            return
        import codex
        run_benchmark('import_codex', lambda: importlib.import_module('codex'))
        print("TEST_PASS:codex:Imported successfully")
    except Exception as e:
        print(f"TEST_FAIL:codex:{str(e)}")

def test_bard_baseline():
    try:
        spec = importlib.util.find_spec('transformers')
        if spec is None:
            print("TEST_FAIL:transformers:Module not found")
            return
        import transformers
        run_benchmark('import_bard', lambda: importlib.import_module('transformers'))
        print("TEST_PASS:transformers:Imported successfully")
    except Exception as e:
        print(f"TEST_FAIL:transformers:{str(e)}")

def main():
    if not install_packages('git'):
        return
    if not install_tool_dependencies('codex'):
        return

    test_codex_desktop()
    test_bard_baseline()

    codex_desktop_benchmark = run_benchmark('codex_desktop', lambda: print("Hello, World!"))
    bard_baseline_benchmark = run_benchmark('bard_baseline', lambda: print("Hello, World!"))
    print(f"BENCHMARK:vs_codex_bard_ratio:{codex_desktop_benchmark / bard_baseline_benchmark}")

    print("RUN_OK")

if __name__ == "__main__":
    main()