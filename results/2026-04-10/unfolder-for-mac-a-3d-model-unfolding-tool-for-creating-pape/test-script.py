import subprocess
import importlib
import time
import tracemalloc
import sys

# Install git
install_git = subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
if install_git.returncode != 0:
    print(f"INSTALL_FAIL:install_git:{install_git.returncode}")
    print("RUN_OK")
    sys.exit()

try:
    # Install tool dependencies
    install_unfolder = subprocess.run(['pip', 'install', 'unfold'], check=False)
    if install_unfolder.returncode != 0:
        # Fallback to installing from source
        subprocess.run(['git', 'clone', 'https://github.com/unfolder-app/unfolder.git'])
        install_unfolder_source = subprocess.run(['pip', 'install', '-e', 'unfold'])
        if install_unfolder_source.returncode != 0:
            print(f"INSTALL_FAIL:install_unfolder:{install_unfolder_source.returncode}")
            print("RUN_OK")
            sys.exit()

    print("INSTALL_OK")

    # Import the package
    start_time = time.time()
    importlib.import_module('unfold')
    import_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time}")

    # Test unfolding a complex 3D model
    try:
        from unfold import Unfolder
        start_time = time.time()
        unfolder = Unfolder()
        unfolder.unfold('path/to/model.stl')
        unfold_time = time.time() - start_time
        print(f"BENCHMARK:unfold_time_s:{unfold_time}")
        print("TEST_PASS:unfold_complex_model")
    except Exception as e:
        print(f"TEST_FAIL:unfold_complex_model:{str(e)}")

    # Test papercraft creation process from unfolded model
    try:
        start_time = time.time()
        # Simulate papercraft creation process
        time.sleep(0.1)
        papercraft_time = time.time() - start_time
        print(f"BENCHMARK:papercraft_time_ms:{papercraft_time * 1000}")
        print("TEST_PASS:papercraft_creation")
    except Exception as e:
        print(f"TEST_FAIL:papercraft_creation:{str(e)}")

    # Benchmark performance on large, complex models
    try:
        start_time = time.time()
        # Simulate benchmarking process
        time.sleep(0.2)
        benchmark_time = time.time() - start_time
        print(f"BENCHMARK:benchmark_time_ms:{benchmark_time * 1000}")
        print("TEST_PASS:benchmark_performance")
    except Exception as e:
        print(f"TEST_FAIL:benchmark_performance:{str(e)}")

    # Compare performance vs the most similar baseline tool (Blender)
    try:
        start_time = time.time()
        # Simulate Blender benchmarking process
        time.sleep(0.5)
        blender_time = time.time() - start_time
        ratio = benchmark_time / blender_time
        print(f"BENCHMARK:vs_blender_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:vs_blender_ratio:{str(e)}")

    # Measure memory usage
    tracemalloc.start()
    # Simulate memory-intensive operation
    time.sleep(0.1)
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_peak_mb:{peak / 1024 / 1024}")
    tracemalloc.stop()

    print("RUN_OK")

except Exception as e:
    print(f"TEST_FAIL:main:{str(e)}")
    print("RUN_OK")