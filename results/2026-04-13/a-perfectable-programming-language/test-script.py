import subprocess
import time
import tracemalloc
import os

def install_dependencies():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL: failed to install dependencies {e}')

def clone_and_build_repo():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/leanprover/lean.git'], check=True)
        os.chdir('lean')
        subprocess.run(['make', 'build'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL: failed to clone and build Lean {e}')

def test_hello_world():
    try:
        start_time = time.time()
        subprocess.run(['./build/lean', './src/HelloWorld.lean'], check=True)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:hello_world_ms:{execution_time:.2f}')
        print('TEST_PASS:hello_world')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:hello_world: failed to run hello world {e}')

def test_type_system():
    try:
        start_time = time.time()
        # Create a complex example to test Lean's type system
        with open('type_system_test.lean', 'w') as f:
            f.write('''
            def id (α : Type) (x : α) : α := x
            def id_id (α : Type) (x : α) : α := id (id x)
            ''')
        subprocess.run(['./build/lean', 'type_system_test.lean'], check=True)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:type_system_test_ms:{execution_time:.2f}')
        print('TEST_PASS:type_system')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:type_system: failed to test Lean\'s type system {e}')

def compare_with_baseline():
    try:
        # Measure time to compile and run a simple program in Python
        start_time = time.time()
        subprocess.run(['python', '-c', 'print("Hello World")'], check=True)
        end_time = time.time()
        python_execution_time = (end_time - start_time) * 1000
        # Measure time to compile and run a simple program in Lean
        start_time = time.time()
        subprocess.run(['./build/lean', './src/HelloWorld.lean'], check=True)
        end_time = time.time()
        lean_execution_time = (end_time - start_time) * 1000
        ratio = lean_execution_time / python_execution_time
        print(f'BENCHMARK:vs_python_hello_world_ratio:{ratio:.2f}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:compare_with_baseline: failed to compare with Python {e}')

def measure_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['./build/lean', './src/HelloWorld.lean'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_mb:{peak / 10**6:.2f}')
    except subprocess.CalledProcessError as e:
        print(f'TEST_FAIL:measure_memory_usage: failed to measure memory usage {e}')

def count_lines_of_code():
    try:
        lines = sum(1 for _ in open('src/HelloWorld.lean', 'r'))
        print(f'BENCHMARK:loc_count:{lines}')
    except FileNotFoundError as e:
        print(f'TEST_FAIL:count_lines_of_code: failed to count lines of code {e}')

def count_test_files():
    try:
        files = len([name for name in os.listdir('.') if name.endswith('.lean')])
        print(f'BENCHMARK:test_files_count:{files}')
    except FileNotFoundError as e:
        print(f'TEST_FAIL:count_test_files: failed to count test files {e}')

def main():
    install_dependencies()
    clone_and_build_repo()
    test_hello_world()
    test_type_system()
    compare_with_baseline()
    measure_memory_usage()
    count_lines_of_code()
    count_test_files()
    print('RUN_OK')

if __name__ == '__main__':
    main()