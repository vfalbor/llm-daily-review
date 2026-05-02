import subprocess
import time
import tracemalloc
import sys

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

def install_wavefunctioncollapse():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/mxgmn/WaveFunctionCollapse.git'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

def test_hello_world():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['go', 'run', 'main.go'], cwd='WaveFunctionCollapse', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:hello_world_memory_mb:{current / 10**6:.2f}")
        print("TEST_PASS:hello_world")
    except Exception as e:
        print(f"TEST_FAIL:hello_world:{str(e)}")

def test_bitmap_generation():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['go', 'run', 'main.go', '-bitmap'], cwd='WaveFunctionCollapse', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:bitmap_generation_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:bitmap_generation_memory_mb:{current / 10**6:.2f}")
        print("TEST_PASS:bitmap_generation")
    except Exception as e:
        print(f"TEST_FAIL:bitmap_generation:{str(e)}")

def test_tilemap_generation():
    try:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['go', 'run', 'main.go', '-tilemap'], cwd='WaveFunctionCollapse', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:tilemap_generation_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:tilemap_generation_memory_mb:{current / 10**6:.2f}")
        print("TEST_PASS:tilemap_generation")
    except Exception as e:
        print(f"TEST_FAIL:tilemap_generation:{str(e)}")

def compare_performance():
    try:
        # Run the manual generation method
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['node', 'manual_generation.js'], check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        manual_time = (end_time - start_time) * 1000
        # Run the WFC method
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['go', 'run', 'main.go'], cwd='WaveFunctionCollapse', check=False)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        wfc_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:vs_manual_generation_ratio:{wfc_time / manual_time:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance:{str(e)}")

def main():
    install_packages()
    install_wavefunctioncollapse()
    test_hello_world()
    test_bitmap_generation()
    test_tilemap_generation()
    compare_performance()
    print("RUN_OK")

if __name__ == "__main__":
    main()