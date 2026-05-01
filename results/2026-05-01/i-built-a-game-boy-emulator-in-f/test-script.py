import subprocess
import time
import tracemalloc
import sys

def install_apk_packages(package_names):
    for pkg in package_names:
        try:
            subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
            print("INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:{e}")

def install_tool_dependencies():
    try:
        subprocess.run(['npm', 'install', 'npm@latest'], check=True)
        subprocess.run(['cargo', 'update'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def clone_fame_boy_repository():
    try:
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/nickkossolapov/fame-boy.git'], check=True)
        end_time = time.time()
        elapsed_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:clone_time_ms:{elapsed_time:.2f}")
        print("TEST_PASS:clone_fame_boy_repository")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:clone_fame_boy_repository:{e}")

def measure_memory_usage():
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['git', 'clone', 'https://github.com/nickkossolapov/fame-boy.git'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    print(f"BENCHMARK:execution_time_ms:{(end_time - start_time) * 1000:.2f}")

def measure_execution_time():
    start_time = time.time()
    subprocess.run(['git', 'clone', 'https://github.com/nickkossolapov/fame-boy.git'], check=True)
    end_time = time.time()
    elapsed_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:execution_time_ms:{elapsed_time:.2f}")

def measure_file_count():
    try:
        file_count = len(subprocess.run(['git', 'ls-files', '-z'], check=True, stdout=subprocess.PIPE).stdout.split(b'\0')) - 1
        print(f"BENCHMARK:file_count:{file_count}")
    except subprocess.CalledProcessError as e:
        print(f"BENCHMARK:file_count:0")

def compare_performance():
    try:
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/nickkossolapov/fame-boy.git'], check=True)
        end_time = time.time()
        elapsed_time = (end_time - start_time) * 1000
        baseline_time = 1000  # Replace with baseline time
        ratio = elapsed_time / baseline_time
        print(f"BENCHMARK:vs_baseline_time_ms:{ratio:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"BENCHMARK:vs_baseline_time_ms:0")

def main():
    package_names = ['nodejs', 'npm', 'git', 'cargo', 'rust']
    install_apk_packages(package_names)
    install_tool_dependencies()
    clone_fame_boy_repository()
    measure_memory_usage()
    measure_execution_time()
    measure_file_count()
    compare_performance()
    print("RUN_OK")

if __name__ == "__main__":
    main()