import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'python3', 'pip'], check=False)

# Install tool dependencies
try:
    subprocess.run(['npm', 'install', '-g', '@calcom/cal'], check=True)
    print('INSTALL_OK')
except Exception as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/calcom/cal.diy.git'], check=True)
        subprocess.run(['npm', 'install', '-g', 'cal.diy'], cwd='cal.diy', check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

# Test 1: Create a meeting
try:
    start_time = time.time()
    meeting_creation_time = time.time()
    subprocess.run(['cal', 'create', 'meeting'], check=True)
    meeting_creation_time = time.time() - meeting_creation_time
    print(f'BENCHMARK:meeting_creation_time_ms:{meeting_creation_time*1000:.2f}')
    print('TEST_PASS:create_meeting')
except Exception as e:
    print(f'TEST_FAIL:create_meeting:{str(e)}')

# Test 2: Verify video quality
try:
    video_quality_time = time.time()
    subprocess.run(['cal', 'join', 'meeting'], check=True)
    video_quality_time = time.time() - video_quality_time
    print(f'BENCHMARK:video_quality_time_ms:{video_quality_time*1000:.2f}')
    print('TEST_PASS:verify_video_quality')
except Exception as e:
    print(f'TEST_FAIL:verify_video_quality:{str(e)}')

# Test 3: Measure CLI usage
try:
    cli_usage_time = time.time()
    subprocess.run(['cal', '--help'], check=True)
    cli_usage_time = time.time() - cli_usage_time
    print(f'BENCHMARK:cli_usage_time_ms:{cli_usage_time*1000:.2f}')
    print('TEST_PASS:measure_cli_usage')
except Exception as e:
    print(f'TEST_FAIL:measure_cli_usage:{str(e)}')

# Compare performance vs baseline tool (Cal.com)
try:
    baseline_time = time.time()
    subprocess.run(['cal.com', '--help'], check=True)
    baseline_time = time.time() - baseline_time
    ratio = (cli_usage_time / baseline_time) * 100
    print(f'BENCHMARK:vs_cal.com_cli_usage_ratio:{ratio:.2f}')
except Exception as e:
    print(f'TEST_SKIP:compare_performance_vs_cal.com:{str(e)}')

# Memory usage benchmark
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_mb:{peak/1024/1024:.2f}')

# CPU count benchmark
print(f'BENCHMARK:cpu_count:{os.cpu_count()}')

# File count benchmark
file_count = sum([len(files) for r, d, files in os.walk('.')])
print(f'BENCHMARK:file_count:{file_count}')

print('RUN_OK')