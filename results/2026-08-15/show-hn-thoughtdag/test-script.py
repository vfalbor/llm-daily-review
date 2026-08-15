import subprocess
import time
import tracemalloc
from thoughtdag import ThoughtDAG

def install_thoughtdag():
    try:
        subprocess.run(['pip', 'install', 'thoughtdag'], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{e}')
        try:
            subprocess.run(['git', 'clone', 'https://github.com/chenxiachan/thoughtdag.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './thoughtdag'], check=True)
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{e}')

def test_import_time():
    try:
        start_time = time.time()
        import thoughtdag
        end_time = time.time()
        benchmark_name = 'import_time_ms'
        benchmark_value = (end_time - start_time) * 1000
        print(f'BENCHMARK:{benchmark_name}:{benchmark_value:.2f}')
        print(f'TEST_PASS:{benchmark_name}')
    except Exception as e:
        print(f'TEST_FAIL:test_import_time:{e}')

def test_thoughtdag_latency():
    try:
        start_time = time.time()
        thoughtdag = ThoughtDAG()
        thoughtdag.query('synthetic_data')
        end_time = time.time()
        benchmark_name = 'query_latency_ms'
        benchmark_value = (end_time - start_time) * 1000
        print(f'BENCHMARK:{benchmark_name}:{benchmark_value:.2f}')
        print(f'TEST_PASS:test_thoughtdag_latency')
    except Exception as e:
        print(f'TEST_FAIL:test_thoughtdag_latency:{e}')

def test_memory_usage():
    try:
        tracemalloc.start()
        thoughtdag = ThoughtDAG()
        thoughtdag.query('synthetic_data')
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        benchmark_name = 'memory_usage Mb'
        benchmark_value = current / (1024 * 1024)
        print(f'BENCHMARK:{benchmark_name}:{benchmark_value:.2f}')
        print(f'TEST_PASS:test_memory_usage')
    except Exception as e:
        print(f'TEST_FAIL:test_memory_usage:{e}')

def benchmark_vs_llama_index():
    try:
        import llama_index
        start_time = time.time()
        llama_index.query('synthetic_data')
        end_time = time.time()
        llama_index_latency = (end_time - start_time) * 1000
        start_time = time.time()
        thoughtdag = ThoughtDAG()
        thoughtdag.query('synthetic_data')
        end_time = time.time()
        thoughtdag_latency = (end_time - start_time) * 1000
        benchmark_name = 'vs_llama_index_latency_ratio'
        benchmark_value = thoughtdag_latency / llama_index_latency
        print(f'BENCHMARK:{benchmark_name}:{benchmark_value:.2f}')
    except Exception as e:
        print(f'BENCHMARK:vs_llama_index_latency_ratio:NaN')

def main():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    install_thoughtdag()
    test_import_time()
    test_thoughtdag_latency()
    test_memory_usage()
    benchmark_vs_llama_index()
    print('RUN_OK')

if __name__ == '__main__':
    main()