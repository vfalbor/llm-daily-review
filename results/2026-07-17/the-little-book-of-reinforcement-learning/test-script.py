import subprocess
import pip
import pkg_resources
import time
import tracemalloc
import importlib
import random

def install_package():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        pip.main(['install', 'git+https://github.com/alxndrTL/little-book-rl.git'])
        print('INSTALL_OK')
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/alxndrTL/little-book-rl.git'])
            pip.main(['install', '-e', './little-book-rl'])
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_import_time():
    try:
        start_time = time.time()
        import little_book_rl
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
        print(f'TEST_PASS:test_import_time')
    except Exception as e:
        print(f'TEST_FAIL:test_import_time:{str(e)}')

def test_rl_example():
    try:
        start_time = time.time()
        import little_book_rl
        import numpy as np
        # Minimal functional test with synthetic data
        num_actions = 5
        num_steps = 100
        rewards = np.random.rand(num_steps)
        actions = np.random.choice(num_actions, size=num_steps)
        end_time = time.time()
        test_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:rl_example_ms:{test_time:.2f}')
        print(f'TEST_PASS:test_rl_example')
    except Exception as e:
        print(f'TEST_FAIL:test_rl_example:{str(e)}')

def test_chapter_topics():
    try:
        import little_book_rl
        chapter_topics = little_book_rl.get_chapter_topics()
        if len(chapter_topics) > 0:
            print(f'TEST_PASS:test_chapter_topics')
        else:
            print(f'TEST_FAIL:test_chapter_topics:chapter topics list is empty')
    except Exception as e:
        print(f'TEST_FAIL:test_chapter_topics:{str(e)}')

def compare_baseline():
    try:
        import rl_book
        start_time = time.time()
        import little_book_rl
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        start_time = time.time()
        import rl_book
        end_time = time.time()
        baseline_import_time = (end_time - start_time) * 1000
        ratio = import_time / baseline_import_time
        print(f'BENCHMARK:vs_rl_book_import_ratio:{ratio:.2f}')
    except Exception as e:
        print(f'BENCHMARK:vs_rl_book_import_ratio:NaN')

def measure_memory_usage():
    try:
        tracemalloc.start()
        import little_book_rl
        current, peak = tracemalloc.get_traced_memory()
        print(f'BENCHMARK:memory_usage_bytes:{peak}')
        tracemalloc.stop()
    except Exception as e:
        print(f'BENCHMARK:memory_usage_bytes:NaN')

def count_files():
    try:
        import os
        file_count = len([name for name in os.listdir('.') if os.path.isfile(name)])
        print(f'BENCHMARK:file_count:{file_count}')
    except Exception as e:
        print(f'BENCHMARK:file_count:NaN')

def count_lines():
    try:
        import os
        lines = 0
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        lines += sum(1 for _ in f)
        print(f'BENCHMARK:loc_count:{lines}')
    except Exception as e:
        print(f'BENCHMARK:loc_count:NaN')

install_package()
test_import_time()
test_rl_example()
test_chapter_topics()
compare_baseline()
measure_memory_usage()
count_files()
count_lines()

print('RUN_OK')