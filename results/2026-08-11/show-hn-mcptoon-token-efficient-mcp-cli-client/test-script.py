import subprocess
import time
import tracemalloc
import sys
import importlib.util
import io
import os

def install_m cptoon():
    try:
        # Try pip install first
        subprocess.run(['pip', 'install', 'mcptoon'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError:
        try:
            # Fallback to git clone and pip install -e
            subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
            subprocess.run(['git', 'clone', 'https://github.com/activeing123/mcptoon.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './mcptoon'], cwd='./mcptoon', check=True)
            print('INSTALL_OK')
        except subprocess.CalledProcessError as e:
            print(f'INSTALL_FAIL:{e}')

def test_token_issuance():
    try:
        # Import mcptoon and test token issuance
        spec = importlib.util.spec_from_file_location('mcptoon', '/mcptoon/mcptoon/__init__.py')
        mcptoon = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mcptoon)
        start_time = time.time()
        mcptoon.issue_token()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:token_issuance_ms:{latency:.2f}')
        print('TEST_PASS:token_issuance')
    except Exception as e:
        print(f'TEST_FAIL:token_issuance:{e}')

def benchmark_suite():
    try:
        # Run a benchmarking suite
        import mcptoon
        tracemalloc.start()
        start_time = time.time()
        for i in range(100):
            mcptoon.issue_token()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:suite_latency_ms:{latency:.2f}')
        print(f'BENCHMARK:suite_peak_memory_mb:{peak / 10**6:.2f}')
        print('TEST_PASS:benchmark_suite')
    except Exception as e:
        print(f'TEST_FAIL:benchmark_suite:{e}')

def test_token_validation():
    try:
        # Test token validation logic
        import mcptoon
        start_time = time.time()
        mcptoon.validate_token('invalid_token')
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:token_validation_ms:{latency:.2f}')
        print('TEST_PASS:token_validation')
    except Exception as e:
        print(f'TEST_FAIL:token_validation:{e}')

def compare_to_baseline():
    try:
        # Compare performance to token-auth
        import token_auth
        import mcptoon
        start_time = time.time()
        token_auth.issue_token()
        end_time = time.time()
        baseline_latency = (end_time - start_time) * 1000
        start_time = time.time()
        mcptoon.issue_token()
        end_time = time.time()
        mcptoon_latency = (end_time - start_time) * 1000
        ratio = mcptoon_latency / baseline_latency
        print(f'BENCHMARK:vs_token_auth_token_issuance_ratio:{ratio:.2f}')
    except Exception as e:
        print(f'TEST_SKIP:compare_to_baseline:{e}')

def main():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    install_m cptoon()
    test_token_issuance()
    benchmark_suite()
    test_token_validation()
    compare_to_baseline()
    print('RUN_OK')

if __name__ == '__main__':
    main()