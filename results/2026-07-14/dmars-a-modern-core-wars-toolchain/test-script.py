import subprocess
import time
import tracemalloc
import importlib.util
import sys

def install_packages(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=True)
        print(f"INSTALL_OK: {package}")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL: {package} - {str(e)}")

def install_tool(tool):
    try:
        subprocess.run(['pip', 'install', tool], check=True)
        print(f"INSTALL_OK: {tool}")
    except subprocess.CalledProcessError as e:
        try:
            subprocess.run(['git', 'clone', f'https://github.com/{tool}.git'], check=True)
            subprocess.run(['pip', 'install', '-e', f'./{tool}'], check=True)
            print(f"INSTALL_OK: {tool}")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL: {tool} - {str(e)}")

def run_test(name):
    try:
        # Synthetic data for minimal functional test
        from dmars import core
        core_code = """
            ;redcode
            ;name   Dmars Test
            ;author Your Name
            ORG      START
        """
        start_time = time.time()
        core.load(core_code)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:core_operation_latency_ms:{latency:.2f}")
        print(f"TEST_PASS: {name}")
    except Exception as e:
        print(f"TEST_FAIL: {name} - {str(e)}")

def measure_import_time():
    start_time = time.time()
    import dmars
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{latency:.2f}")

def measure_install_time():
    start_time = time.time()
    install_tool('dmars')
    end_time = time.time()
    latency = (end_time - start_time)
    print(f"BENCHMARK:install_time_s:{latency:.2f}")

def compare_with_baseline():
    try:
        from redcode import core
        core_code = """
            ;redcode
            ;name   Redcode Test
            ;author Your Name
            ORG      START
        """
        start_time = time.time()
        core.load(core_code)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        baseline_latency = latency
        import dmars
        start_time = time.time()
        dmars.core.load(core_code)
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        ratio = latency / baseline_latency
        print(f"BENCHMARK:vs_redcode_latency_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL: compare_with_baseline - {str(e)}")

def main():
    install_packages('git')
    measure_install_time()
    measure_import_time()
    run_test('Dmars Minimal Test')
    compare_with_baseline()

    tracemalloc.start()
    run_test('Dmars Memory Test')
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    tracemalloc.stop()

    print("RUN_OK")

if __name__ == '__main__':
    main()