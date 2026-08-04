import subprocess
import time
import tracemalloc
import os

# Install system packages
start_time = time.time()
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
end_time = time.time()
install_time = end_time - start_time
print(f"BENCHMARK:install_time_s:{install_time:.2f}")

# Install tool dependencies
start_time = time.time()
try:
    subprocess.run(['npm', 'install', 'ffmpeg-cli'], check=True)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:FFmpeg installation via npm failed")
    subprocess.run(['git', 'clone', 'https://github.com/FFmpeg/FFmpeg.git'], check=True)
    subprocess.run(['cargo', 'build', '--release'], check=True, cwd='FFmpeg')
end_time = time.time()
install_time = end_time - start_time
print(f"BENCHMARK:install_time_s:{install_time:.2f}")

# Run FFmpeg version test
start_time = time.time()
try:
    subprocess.run(['ffmpeg', '--version'], check=True)
    print("TEST_PASS:FFmpeg version test")
except subprocess.CalledProcessError:
    print("TEST_FAIL:FFmpeg version test:FFmpeg not installed correctly")
end_time = time.time()
test_time = end_time - start_time
print(f"BENCHMARK:version_test_ms:{test_time*1000:.2f}")

# Create a project and build it using FFmpeg
start_time = time.time()
try:
    # Create a sample video file
    subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'testsrc', '-t', '5', 'sample.mp4'], check=True)
    print("TEST_PASS:Create project test")
except subprocess.CalledProcessError:
    print("TEST_FAIL:Create project test:FFmpeg failed to create project")
end_time = time.time()
test_time = end_time - start_time
print(f"BENCHMARK:project_creation_ms:{test_time*1000:.2f}")

# Compare performance vs baseline tool (e.g., avconv)
start_time = time.time()
try:
    subprocess.run(['avconv', '-f', 'lavfi', '-i', 'testsrc', '-t', '5', 'sample.mp4'], check=True)
    end_time = time.time()
    baseline_time = end_time - start_time
    ratio = test_time / baseline_time
    print(f"BENCHMARK:vs_avconv_project_creation_ratio:{ratio:.2f}")
except subprocess.CalledProcessError:
    print("TEST_SKIP:Baseline performance test:avconv not installed")

# Measure memory usage
tracemalloc.start()
start_time = time.time()
subprocess.run(['ffmpeg', '-f', 'lavfi', '-i', 'testsrc', '-t', '5', 'sample.mp4'], check=True)
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")
print(f"BENCHMARK:execution_time_ms:{(end_time - start_time)*1000:.2f}")

# Count lines of code
try:
    loc_count = subprocess.run(['git', 'ls-files', '-z'], check=True, capture_output=True, text=True).stdout.count('\0')
    print(f"BENCHMARK:loc_count:{loc_count}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:Count lines of code:Git not installed")

# Count test files
try:
    test_files_count = len(subprocess.run(['git', 'ls-files', '--', 'tests'], check=True, capture_output=True, text=True).stdout.splitlines())
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except subprocess.CalledProcessError:
    print("TEST_FAIL:Count test files:Git not installed")

print("RUN_OK")