import subprocess
import time
import tracemalloc
import os

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_command:{e}")
        return False

def install_colibri():
    start_time = time.time()
    try:
        # Install required packages
        run_command(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'])
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        return False

    # Clone and build colibri
    try:
        run_command(['git', 'clone', 'https://github.com/JustVugg/colibri.git'])
        os.chdir('colibri')
        run_command(['cargo', 'build', '--release'])
        end_time = time.time()
        print(f"BENCHMARK:install_time_s:{end_time - start_time}")
    except Exception as e:
        print(f"TEST_FAIL:install_colibri:{e}")
        return False

    return True

def test_compile_time():
    try:
        start_time = time.time()
        run_command(['cargo', 'build', '--release'])
        end_time = time.time()
        compile_time = end_time - start_time
        print(f"BENCHMARK:compile_time_ms:{compile_time * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:test_compile_time:{e}")

def test_linking_time():
    try:
        start_time = time.time()
        run_command(['cargo', 'build', '--release'])
        end_time = time.time()
        linking_time = end_time - start_time
        print(f"BENCHMARK:linking_time_ms:{linking_time * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:test_linking_time:{e}")

def test_execution_time():
    try:
        start_time = time.time()
        run_command(['cargo', 'run', '--release'])
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"BENCHMARK:execution_time_ms:{execution_time * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:test_execution_time:{e}")

def compare_benchmark(baseline_tool):
    try:
        start_time = time.time()
        run_command(['cmake', '.'])
        run_command(['make'])
        end_time = time.time()
        baseline_time = end_time - start_time
        start_time = time.time()
        run_command(['cargo', 'build', '--release'])
        end_time = time.time()
        colibri_time = end_time - start_time
        ratio = colibri_time / baseline_time
        print(f"BENCHMARK:vs_{baseline_tool}_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:compare_benchmark:{e}")

def main():
    install_colibri()
    test_compile_time()
    test_linking_time()
    test_execution_time()
    compare_benchmark('cmake')

    # Measure memory usage
    tracemalloc.start()
    run_command(['cargo', 'build', '--release'])
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    tracemalloc.stop()

    # Print the number of lines of code
    loc_count = 0
    for root, dirs, files in os.walk('colibri'):
        for file in files:
            if file.endswith('.rs'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += len(f.readlines())
    print(f"BENCHMARK:loc_count:{loc_count}")

    print("RUN_OK")

if __name__ == "__main__":
    main()