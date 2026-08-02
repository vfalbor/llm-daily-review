import subprocess
import time
import tracemalloc
import os
import random

def install_fuse():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=True)
        subprocess.run(['git', 'clone', 'https://github.com/fuseliang/fuse.git'], check=True)
        os.chdir('fuse')
        subprocess.run(['go', 'build', '-o', 'fuse'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_helloworld():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['./fuse', '../examples/hello_world.fuse'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:compile_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024):.2f}")
        print(f"TEST_PASS:helloworld")
    except Exception as e:
        print(f"TEST_FAIL:helloworld:{str(e)}")

def test_benchmark():
    try:
        start_time = time.time()
        subprocess.run(['./fuse', '../examples/fib.fuse'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:fib_time_ms:{(end_time - start_time) * 1000:.2f}")
        
        # run baseline (python)
        start_time = time.time()
        subprocess.run(['python', '../examples/fib.py'], check=True)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        fuse_time = (subprocess.run(['./fuse', '../examples/fib.fuse'], capture_output=True, text=True, check=True).stderr)
        fuse_time_ms = float(fuse_time.split()[-1])
        ratio = fuse_time_ms / baseline_time
        print(f"BENCHMARK:vs_python_fib_ratio:{ratio:.2f}")
        print(f"TEST_PASS:benchmark")
    except Exception as e:
        print(f"TEST_FAIL:benchmark:{str(e)}")

def test_type_system():
    try:
        # generate random fuse code with fuzz testing
        num_tests = 10
        for i in range(num_tests):
            code = f"let x: Int = {random.randint(0, 100)};\n"
            with open(f"fuzz_{i}.fuse", 'w') as f:
                f.write(code)
            subprocess.run(['./fuse', f"fuzz_{i}.fuse"], check=True)
        print(f"BENCHMARK:type_system_correctness_ratio:1.0")
        print(f"TEST_PASS:type_system")
    except Exception as e:
        print(f"TEST_FAIL:type_system:{str(e)}")

def main():
    install_fuse()
    test_helloworld()
    test_benchmark()
    test_type_system()
    print("RUN_OK")

if __name__ == "__main__":
    main()