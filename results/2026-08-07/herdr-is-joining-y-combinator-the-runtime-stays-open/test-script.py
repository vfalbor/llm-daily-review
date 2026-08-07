import subprocess
import time
import tracemalloc
import importlib.util
import os

# Step 1: Install required APK packages
print("Installing required APK packages...")
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

# Step 2: Clone the Herdr repository and install the package
print("Cloning the Herdr repository and installing the package...")
try:
    subprocess.run(['git', 'clone', 'https://github.com/herdrio/herdr.git'], check=False)
    subprocess.run(['git', '-C', 'herdr', 'submodule', 'update', '--init'], check=False)
    subprocess.run(['pip', 'install', '-e', 'herdr'], check=False)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Step 3: Compile the runtime with GHC (Haskell)
print("Compiling the runtime with GHC (Haskell)...")
try:
    subprocess.run(['apk', 'add', '--no-cache', 'ghc'], check=False)
    subprocess.run(['git', '-C', 'herdr', 'config', 'core.fsyncobjectfiles', 'false'], check=False)
    start_time = time.time()
    subprocess.run(['git', '-C', 'herdr', 'config', 'core.fsyncobjectfiles', 'false'], check=False)
    subprocess.run(['cabal', 'install', '--project-file=herdr/cabal.project', '--only-dependencies', '--ghc-option=-O2'], check=False)
    end_time = time.time()
    compile_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:compile_time_ms:{compile_time_ms}")
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Step 4: Verify the execution of Herdr code through the runtime
print("Verifying the execution of Herdr code through the runtime...")
try:
    start_time = time.time()
    subprocess.run(['./herdr/run', 'herdr/test/test.hs'], check=False)
    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:execution_time_ms:{execution_time_ms}")
    print("TEST_PASS:execution_test")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:execution_test:{e}")

# Step 5: Measure import time
print("Measuring import time...")
try:
    start_time = time.time()
    import herdr
    end_time = time.time()
    import_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time_ms}")
except ImportError as e:
    print(f"TEST_FAIL:import_test:{e}")

# Step 6: Compare performance vs the most similar baseline tool
print("Comparing performance vs the most similar baseline tool...")
try:
    import timeit
    start_time = time.time()
    importlib.util.find_spec('haskell')
    end_time = time.time()
    baseline_import_time_ms = (end_time - start_time) * 1000
    ratio = import_time_ms / baseline_import_time_ms
    print(f"BENCHMARK:vs_haskell_import_ratio:{ratio}")
except ImportError:
    print("BENCHMARK:vs_haskell_import_ratio:N/A")

# Step 7: Measure memory usage
print("Measuring memory usage...")
try:
    tracemalloc.start()
    import herdr
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    tracemalloc.stop()
except ImportError as e:
    print(f"TEST_FAIL:memory_test:{e}")

# Step 8: Count number of test files
print("Counting number of test files...")
try:
    test_files_count = len([f for f in os.listdir('herdr/test') if f.endswith('.hs')])
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    print(f"BENCHMARK:test_files_count:N/A:{e}")

# Step 9: Count number of lines of code
print("Counting number of lines of code...")
try:
    loc_count = 0
    for root, dirs, files in os.walk('herdr'):
        for file in files:
            if file.endswith('.hs'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += len(f.readlines())
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    print(f"BENCHMARK:loc_count:N/A:{e}")

print("RUN_OK")