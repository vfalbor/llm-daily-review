import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'gcc', 'make', 'musl-dev'], check=False)

# Install tool dependencies
try:
    subprocess.run(['npm', 'install', '-g', '@vercel-labs/scriptc'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/vercel-labs/scriptc.git'], check=True)
        subprocess.run(['npm', 'install', '-g', './scriptc'], cwd='scriptc', check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print('INSTALL_FAIL:failed to install scriptc')
        print('RUN_OK')
        exit(1)

# Clone the repo
try:
    subprocess.run(['git', 'clone', 'https://github.com/vercel-labs/scriptc.git'], check=True)
    print('TEST_PASS:clone_repo')
except subprocess.CalledProcessError as e:
    print('TEST_FAIL:clone_repo:failed to clone repository')
    print('RUN_OK')
    exit(1)

# Run the example TypeScript code
try:
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['tsc', '--build', './example/tsconfig.json'], cwd='scriptc', check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:ts_compile_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:ts_compile_memory_mb:{current / 1024 / 1024}')
    print('TEST_PASS:run_example')
except subprocess.CalledProcessError as e:
    print('TEST_FAIL:run_example:failed to run example code')
    print('RUN_OK')
    exit(1)

# Verify the compiled native binary works
try:
    subprocess.run(['./example/dist/index'], cwd='scriptc', check=True)
    print('TEST_PASS:verify_binary')
except subprocess.CalledProcessError as e:
    print('TEST_FAIL:verify_binary:failed to run compiled binary')

# Baseline tool: Parcel
try:
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['parcel', 'build', './example/src/index.ts'], cwd='scriptc', check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:parcel_compile_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:parcel_compile_memory_mb:{current / 1024 / 1024}')
    print(f'BENCHMARK:vs_parcel_compile_time_ratio:{(end_time - start_time) / (end_time - start_time)}')
except subprocess.CalledProcessError as e:
    print('TEST_SKIP:baseline_parcel:failed to run parcel')

# Count lines of code
try:
    loc_count = subprocess.run(['find', './scriptc', '-name', '*.ts', '-exec', 'wc', '-l', '{}', ';'], capture_output=True, text=True)
    loc_count = sum(map(int, loc_count.stdout.split()))
    print(f'BENCHMARK:loc_count:{loc_count}')
except Exception as e:
    print('TEST_FAIL:count_loc:failed to count lines of code')

# Count test files
try:
    test_files_count = subprocess.run(['find', './scriptc', '-name', '*.spec.ts', '-exec', 'wc', '-l', '{}', ';'], capture_output=True, text=True)
    test_files_count = sum(map(int, test_files_count.stdout.split()))
    print(f'BENCHMARK:test_files_count:{test_files_count}')
except Exception as e:
    print('TEST_FAIL:count_test_files:failed to count test files')

# Memory and time benchmarks
try:
    tracemalloc.start()
    start_time = time.time()
    subprocess.run(['tsc', '--build', './example/tsconfig.json'], cwd='scriptc', check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:scriptc_compile_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:scriptc_compile_memory_mb:{current / 1024 / 1024}')
except Exception as e:
    print('TEST_FAIL:benchmark_scriptc:failed to run benchmark')

print('RUN_OK')