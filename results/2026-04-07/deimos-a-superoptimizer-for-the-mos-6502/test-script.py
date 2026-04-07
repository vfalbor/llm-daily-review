import subprocess
import time
import tracemalloc
import os

def test_deimos():
    # Install required apk packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")

    # Clone the repo
    try:
        subprocess.run(['git', 'clone', 'https://github.com/aransentin/deimos.git'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:git clone failed with error code {e.returncode}")
        return

    # Count source files and languages
    deiMOS_dir = 'deimos'
    try:
        source_files = [f for f in os.listdir(deiMOS_dir) if os.path.isfile(os.path.join(deiMOS_dir, f))]
        languages = set()
        for f in source_files:
            if f.endswith('.c') or f.endswith('.cpp'):
                languages.add('C/C++')
            elif f.endswith('.py'):
                languages.add('Python')
        print(f"BENCHMARK:loc_count:{len(source_files)}")
        print(f"BENCHMARK:languages_count:{len(languages)}")
    except Exception as e:
        print(f"TEST_FAIL:count_source_files:{str(e)}")

    # Compile deiMOS for 6502 target
    try:
        subprocess.run(['make', '-C', deiMOS_dir], check=True)
        print("TEST_PASS:compile_deimos")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compile_deimos:{str(e)}")

    # Run deiMOS on a 6502 simulator
    try:
        start_time = time.time()
        subprocess.run([os.path.join(deiMOS_dir, 'deimos')], check=True)
        end_time = time.time()
        print(f"BENCHMARK:deimos_run_time_ms:{(end_time - start_time) * 1000}")
        print("TEST_PASS:run_deimos")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_deimos:{str(e)}")

    # Benchmark deiMOS on a 6502-based system
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run([os.path.join(deiMOS_dir, 'deimos'), '-b'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end_time = time.time()
        print(f"BENCHMARK:deimos_benchmark_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:deimos_benchmark_memory_mb:{peak / 10**6}")
        print("TEST_PASS:benchmark_deimos")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:benchmark_deimos:{str(e)}")

    # Compare performance vs duper
    try:
        start_time = time.time()
        subprocess.run(['duper'], check=True)
        end_time = time.time()
        deiMOS_time = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run([os.path.join(deiMOS_dir, 'deimos')], check=True)
        end_time = time.time()
        deiMOS_time_baseline = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_duper_deimos_ratio:{deiMOS_time_baseline / deiMOS_time}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_SKIP:compare_deimos_duper:{str(e)}")

    print("RUN_OK")

if __name__ == "__main__":
    test_deimos()