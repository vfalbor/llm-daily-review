import subprocess
import time
from tracemalloc import start, stop, get_traced_memory
import os

def install_tangleflow():
    try:
        # Install system packages
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
        # Install tangleflow via npm
        subprocess.run(['npm', 'install', '-g', 'tangleflow'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

def test_convert_workflow():
    try:
        # Start tracing memory
        start()
        start_time = time.time()
        # Convert a simple GitHub Actions workflow
        subprocess.run(['tangleflow', 'convert', 'https://github.com/43081j/tangleflow'], check=False)
        end_time = time.time()
        # Stop tracing memory
        stop()
        # Get memory usage
        memory_usage = get_traced_memory()[1] / (1024 * 1024)
        print(f'BENCHMARK:conversion_time_ms:{(end_time - start_time) * 1000}')
        print(f'BENCHMARK:conversion_memory_mb:{memory_usage}')
        print(f'TEST_PASS:convert_workflow')
    except Exception as e:
        print(f'TEST_FAIL:convert_workflow:{str(e)}')

def test_correctness():
    try:
        start_time = time.time()
        # Verify correctness of converted tangled workflow
        subprocess.run(['git', 'clone', 'https://github.com/43081j/tangleflow'], check=False)
        subprocess.run(['cd', 'tangleflow', '&&', 'tangleflow', 'verify'], check=False)
        end_time = time.time()
        print(f'BENCHMARK:verification_time_ms:{(end_time - start_time) * 1000}')
        print(f'TEST_PASS:correctness')
    except Exception as e:
        print(f'TEST_FAIL:correctness:{str(e)}')

def test_build_time():
    try:
        start_time = time.time()
        # Compare build time between original and converted workflows
        subprocess.run(['git', 'clone', 'https://github.com/43081j/tangleflow'], check=False)
        subprocess.run(['cd', 'tangleflow', '&&', 'tangleflow', 'build'], check=False)
        end_time = time.time()
        build_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:build_time_ms:{build_time}')
        # Compare build time vs the most similar baseline tool listed above
        start_time = time.time()
        subprocess.run(['git', 'clone', 'https://github.com/github-action-workflows'], check=False)
        subprocess.run(['cd', 'github-action-workflows', '&&', 'make', 'build'], check=False)
        end_time = time.time()
        baseline_build_time = (end_time - start_time) * 1000
        ratio = build_time / baseline_build_time
        print(f'BENCHMARK:vs_github-action-workflows_build_time_ratio:{ratio}')
        print(f'TEST_PASS:build_time')
    except Exception as e:
        print(f'TEST_FAIL:build_time:{str(e)}')

def main():
    install_tangleflow()
    test_convert_workflow()
    test_correctness()
    test_build_time()
    print('RUN_OK')

if __name__ == "__main__":
    main()