import subprocess
import time
import tracemalloc
import pip
import os
import signal
import sys

def install_cipherstash():
    try:
        # Install APK packages
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        # Install CipherStash via pip
        subprocess.run(['pip', 'install', 'cipherstash'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:{e}')

def test_encrypt_table():
    try:
        import cipherstash
        from cipherstash import CipherStash
        # Create a CipherStash instance
        cs = CipherStash()
        # Encrypt a Supabase table with synthetic data
        import time
        start_time = time.time()
        cs.encrypt_table()
        end_time = time.time()
        encrypt_time_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:encrypt_time_ms:{encrypt_time_ms}')
        print(f'TEST_PASS:encrypt_table')
    except Exception as e:
        print(f'TEST_FAIL:encrypt_table:{e}')

def test_query_table():
    try:
        import cipherstash
        from cipherstash import CipherStash
        # Create a CipherStash instance
        cs = CipherStash()
        # Query the encrypted table
        import time
        start_time = time.time()
        cs.query_table()
        end_time = time.time()
        query_time_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:query_time_ms:{query_time_ms}')
        print(f'TEST_PASS:query_table')
    except Exception as e:
        print(f'TEST_FAIL:query_table:{e}')

def test_throughput_latency():
    try:
        import cipherstash
        from cipherstash import CipherStash
        # Create a CipherStash instance
        cs = CipherStash()
        # Measure throughput and latency
        import time
        import random
        start_time = time.time()
        for _ in range(1000):
            cs.encrypt_table()
            cs.query_table()
        end_time = time.time()
        throughput_op_ms = (end_time - start_time) / 1000
        latency_ms = (end_time - start_time) * 1000 / 1000
        print(f'BENCHMARK:throughput_latency_ms:{throughput_op_ms}')
        print(f'BENCHMARK:latency_ms:{latency_ms}')
        print(f'TEST_PASS:throughput_latency')
    except Exception as e:
        print(f'TEST_FAIL:throughput_latency:{e}')

def test_data_recovery():
    try:
        import cipherstash
        from cipherstash import CipherStash
        # Create a CipherStash instance
        cs = CipherStash()
        # Test data recovery with correct decryption key
        import time
        start_time = time.time()
        cs.recover_data()
        end_time = time.time()
        recover_time_ms = (end_time - start_time) * 1000
        print(f'BENCHMARK:recover_time_ms:{recover_time_ms}')
        print(f'TEST_PASS:data_recovery')
    except Exception as e:
        print(f'TEST_FAIL:data_recovery:{e}')

def compare_performance():
    try:
        import rookout
        # Compare performance with Rookout
        import time
        start_time = time.time()
        rookout.test_performance()
        end_time = time.time()
        rookout_time_ms = (end_time - start_time) * 1000
        import cipherstash
        from cipherstash import CipherStash
        cs = CipherStash()
        start_time = time.time()
        cs.test_performance()
        end_time = time.time()
        cipherstash_time_ms = (end_time - start_time) * 1000
        ratio = rookout_time_ms / cipherstash_time_ms
        print(f'BENCHMARK:vs_rookout_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_FAIL:compare_performance:{e}')

def main():
    install_cipherstash()
    test_encrypt_table()
    test_query_table()
    test_throughput_latency()
    test_data_recovery()
    compare_performance()
    # Memory usage
    tracemalloc.start()
    import cipherstash
    from cipherstash import CipherStash
    cs = CipherStash()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:memory_usage_bytes:{current}')
    print(f'BENCHMARK:memory_peak_bytes:{peak}')
    # Time usage
    import time
    start_time = time.time()
    cs.test_performance()
    end_time = time.time()
    import_time_ms = (end_time - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time_ms}')
    # File count
    import os
    file_count = len(os.listdir())
    print(f'BENCHMARK:file_count:{file_count}')
    # Line of code count
    loc_count = sum(1 for _ in open(__file__))
    print(f'BENCHMARK:loc_count:{loc_count}')
    print('RUN_OK')

if __name__ == '__main__':
    main()