import subprocess
import time
import tracemalloc
import importlib.util
import os
import sys

def install_dependencies():
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    
    # Install tool dependencies
    try:
        subprocess.run(['pip', 'install', 'git-diff-driver'], check=True)
    except subprocess.CalledProcessError:
        # Install from source as fallback
        subprocess.run(['git', 'clone', 'https://github.com/jessitron/git-diff-driver.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './git-diff-driver'], check=True, cwd='./git-diff-driver')

def load_module(module_name):
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        return importlib.util.module_from_spec(spec)
    else:
        return None

def test_basic_functionality():
    try:
        import git_diff_driver
        start_time = time.time()
        # Run a minimal functional test with synthetic data
        git_diff_driver.diff('test.txt', 'test.txt')
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:basic_functionality_latency_ms:{latency_ms:.2f}')
        print(f'TEST_PASS:basic_functionality')
    except Exception as e:
        print(f'TEST_FAIL:basic_functionality:{str(e)}')

def test_edge_cases():
    try:
        import git_diff_driver
        start_time = time.time()
        # Test with binary data
        with open('binary.txt', 'wb') as f:
            f.write(b'\x00\x01\x02')
        git_diff_driver.diff('binary.txt', 'binary.txt')
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:binary_file_latency_ms:{latency_ms:.2f}')
        print(f'TEST_PASS:edge_cases')
    except Exception as e:
        print(f'TEST_FAIL:edge_cases:{str(e)}')

def test_multiple_commits():
    try:
        import git_diff_driver
        start_time = time.time()
        # Simulate multiple commits
        for i in range(10):
            with open(f'file{i}.txt', 'w') as f:
                f.write(f'File {i} content')
            git_diff_driver.diff(f'file{i}.txt', f'file{i}.txt')
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:multiple_commits_latency_ms:{latency_ms:.2f}')
        print(f'TEST_PASS:multiple_commits')
    except Exception as e:
        print(f'TEST_FAIL:multiple_commits:{str(e)}')

def benchmark_import_time():
    start_time = time.time()
    import git_diff_driver
    end_time = time.time()
    import_time_ms = (end_time - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time_ms:.2f}')

def compare_with_baseline():
    # Compare performance with the most similar baseline tool (git)
    start_time = time.time()
    subprocess.run(['git', 'diff', 'test.txt', 'test.txt'], check=True)
    end_time = time.time()
    baseline_latency_ms = (end_time - start_time) * 1000
    try:
        import git_diff_driver
        start_time = time.time()
        git_diff_driver.diff('test.txt', 'test.txt')
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        ratio = latency_ms / baseline_latency_ms
        print(f'BENCHMARK:vs_git_diff_ratio:{ratio:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:compare_with_baseline:{str(e)}')

def main():
    tracemalloc.start()
    install_dependencies()
    print(f'INSTALL_OK')
    benchmark_import_time()
    
    test_basic_functionality()
    test_edge_cases()
    test_multiple_commits()
    
    compare_with_baseline()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{current}')
    print(f'BENCHMARK:peak_memory_usage_bytes:{peak}')
    tracemalloc.stop()
    
    print(f'RUN_OK')

if __name__ == '__main__':
    main()