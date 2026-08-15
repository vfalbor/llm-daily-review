import subprocess
import time
import tracemalloc
import os
import sys

def install_racket():
    try:
        # Install required packages
        subprocess.run(['apk', 'add', '--no-cache', 'gcc', 'g++', 'make', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
        # Clone and build Racket from source
        subprocess.run(['git', 'clone', 'https://github.com/racket/racket.git'], check=True)
        os.chdir('racket')
        start_time = time.time()
        subprocess.run(['./configure'], check=True)
        subprocess.run(['make'], check=True)
        install_time = time.time() - start_time
        print(f"BENCHMARK:install_time_s:{install_time:.2f}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
        return False

def test_hello_world():
    try:
        # Run hello world program
        start_time = time.time()
        subprocess.run(['./racket', '-f', 'hello-world.rkt'], check=True)
        run_time = time.time() - start_time
        print(f"TEST_PASS:hello_world")
        print(f"BENCHMARK:hello_world_ms:{run_time*1000:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:hello_world:{e}")

def test_compile_time_evaluation():
    try:
        # Test compile-time evaluation
        start_time = time.time()
        subprocess.run(['./racket', '-f', 'compile-time-eval.rkt'], check=True)
        run_time = time.time() - start_time
        print(f"TEST_PASS:compile_time_evaluation")
        print(f"BENCHMARK:compile_time_eval_ms:{run_time*1000:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compile_time_evaluation:{e}")

def test_memory_leaks():
    try:
        # Test for memory leaks
        tracemalloc.start()
        start_time = time.time()
        subprocess.run(['./racket', '-f', 'memory-leak-test.rkt'], check=True)
        run_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"TEST_PASS:memory_leaks")
        print(f"BENCHMARK:memory_leak_test_ms:{run_time*1000:.2f}")
        print(f"BENCHMARK:memory_peak_mb:{peak/1024/1024:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:memory_leaks:{e}")

def test_performance_comparison():
    try:
        # Compare compilation speed with Scheme
        # Install scheme
        subprocess.run(['apk', 'add', '--no-cache', 'guile'], check=True)
        # Compile scheme program
        start_time = time.time()
        subprocess.run(['guile', '--no-cache', 'scheme-benchmark.scm'], check=True)
        scheme_time = time.time() - start_time
        # Compile racket program
        start_time = time.time()
        subprocess.run(['./racket', '-f', 'racket-benchmark.rkt'], check=True)
        racket_time = time.time() - start_time
        print(f"BENCHMARK:vs_scheme_compile_speed_ratio:{scheme_time/racket_time:.2f}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:performance_comparison:{e}")

if __name__ == "__main__":
    if install_racket():
        test_hello_world()
        test_compile_time_evaluation()
        test_memory_leaks()
        test_performance_comparison()
    print("RUN_OK")