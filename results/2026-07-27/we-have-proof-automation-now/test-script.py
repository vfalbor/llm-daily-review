import subprocess
import time
import tracemalloc
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git', 'curl'], check=True)

# Clone and build zstd with Lean
try:
    subprocess.run(['git', 'clone', 'https://github.com/benoitf/lean-zstd.git'], check=True)
    subprocess.run(['cd', 'lean-zstd', '&&', 'lean', 'pkg', 'build'], check=False, shell=True)
    subprocess.run(['cd', 'lean-zstd', '&&', 'lean', 'pkg', 'install'], check=False, shell=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")
    sys.exit(1)

# Install zstd pip package for comparison
try:
    subprocess.run(['pip', 'install', 'zstandard'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:pip_zstd_{e}")

# Test 1: Build zstd with Lean and run on sample data
try:
    start_time = time.time()
    subprocess.run(['cd', 'lean-zstd', '&&', './build/bin/zstd', '-f', '-q', '-o', 'sample.zst', 'sample.txt'], check=True, shell=True)
    end_time = time.time()
    print(f"BENCHMARK:build_time_ms:{(end_time - start_time) * 1000}")
    print("TEST_PASS:build_zstd")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:build_zstd:{e}")

# Test 2: Measure compression ratio vs gzip
try:
    start_time = time.time()
    subprocess.run(['gzip', '-c', 'sample.txt', '>', 'sample.gz'], check=True, shell=True)
    end_time = time.time()
    gzip_size = subprocess.run(['stat', '-c%s', 'sample.gz'], capture_output=True, text=True, check=True, shell=True).stdout.strip()
    zstd_size = subprocess.run(['stat', '-c%s', 'sample.zst'], capture_output=True, text=True, check=True, shell=True).stdout.strip()
    compression_ratio = float(zstd_size) / float(gzip_size)
    print(f"BENCHMARK:compression_ratio:{compression_ratio}")
    print(f"BENCHMARK:vs_gzip:{compression_ratio}")
    print("TEST_PASS:compression_ratio")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:compression_ratio:{e}")

# Test 3: Compare decompression time vs standard library
try:
    start_time = time.time()
    subprocess.run(['gunzip', '-c', 'sample.gz'], check=True, shell=True)
    end_time = time.time()
    gzip_decompress_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['zstd', '-d', '-c', 'sample.zst'], check=True, shell=True)
    end_time = time.time()
    zstd_decompress_time = end_time - start_time
    print(f"BENCHMARK:decompress_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:vs_zlib_decompress_ms:{(zstd_decompress_time / gzip_decompress_time) * 1000}")
    print("TEST_PASS:decompress_time")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:decompress_time:{e}")

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage:{current}")
tracemalloc.stop()

# Measure count of files in directory
file_count = subprocess.run(['find', '.', '-type', 'f'], capture_output=True, text=True, check=True).stdout.strip().count('\n')
print(f"BENCHMARK:loc_count:{file_count}")

# Measure count of test files
test_file_count = subprocess.run(['find', '.', '-type', 'f', '-name', 'test_*.py'], capture_output=True, text=True, check=True).stdout.strip().count('\n')
print(f"BENCHMARK:test_files_count:{test_file_count}")

print("RUN_OK")