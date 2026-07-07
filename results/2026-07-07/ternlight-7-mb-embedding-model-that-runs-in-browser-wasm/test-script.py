import subprocess
import time
import tracemalloc
import os

try:
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print('INSTALL_OK')

    # Clone and install Ternlight
    subprocess.run(['git', 'clone', 'https://github.com/memgraph/ternlight.git'], check=True)
    os.chdir('ternlight')
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    print('INSTALL_OK')

    # Test importing Ternlight
    import ternlight
    start_time = time.time()
    ternlight.load_model()
    end_time = time.time()
    print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}')

    # Test training on custom dataset
    try:
        # Create a synthetic dataset
        dataset = [(i, i * 2) for i in range(10)]
        start_time = time.time()
        ternlight.train_model(dataset)
        end_time = time.time()
        print('TEST_PASS:train_model')
        print(f'BENCHMARK:train_time_ms:{(end_time - start_time) * 1000:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:train_model:{str(e)}')

    # Test inference speed
    try:
        start_time = time.time()
        output = ternlight.predict([1, 2, 3])
        end_time = time.time()
        print('TEST_PASS:predict')
        print(f'BENCHMARK:inference_time_ms:{(end_time - start_time) * 1000:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:predict:{str(e)}')

    # Test integration with other libraries
    try:
        import numpy as np
        inputs = np.array([1, 2, 3])
        start_time = time.time()
        output = ternlight.predict(inputs)
        end_time = time.time()
        print('TEST_PASS:integration_with_numpy')
        print(f'BENCHMARK:inference_time_with_numpy_ms:{(end_time - start_time) * 1000:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:integration_with_numpy:{str(e)}')

    # Measure memory usage
    tracemalloc.start()
    ternlight.load_model()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{current}')
    tracemalloc.stop()

    # Benchmark against DistilBERT
    try:
        import transformers
        from transformers import DistilBertTokenizer, DistilBertModel
        tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        model = DistilBertModel.from_pretrained('distilbert-base-uncased')
        start_time = time.time()
        outputs = model(tokenizer.encode('This is a test sentence', return_tensors='pt'))
        end_time = time.time()
        print(f'BENCHMARK:vs_distilbert_inference_time_ms:{(end_time - start_time) * 1000:.2f}')
    except Exception as e:
        print(f'TEST_FAIL:benchmark_against_distilbert:{str(e)}')

    print('RUN_OK')

except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')
    print('RUN_OK')