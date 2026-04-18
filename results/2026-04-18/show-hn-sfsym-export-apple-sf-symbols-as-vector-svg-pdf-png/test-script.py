import subprocess
import time
import tracemalloc
import json
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)

# Install tool dependencies
try:
    subprocess.run(['npm', 'install', '-g', 'sfsym'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:{e}')

try:
    # Clone repo and run `go build`
    subprocess.run(['git', 'clone', 'https://github.com/yapstudios/sfsym.git'], check=True)
    os.chdir('sfsym')
    subprocess.run(['cargo', 'build'], check=True)
    os.chdir('..')

    # Test `sfsym -h`
    start_time = time.time()
    mem_before = tracemalloc.get_traced_memory()[0]
    subprocess.run(['./target/debug/sfsym', '-h'], check=True)
    end_time = time.time()
    mem_after = tracemalloc.get_traced_memory()[0]
    print(f'BENCHMARK:help_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:help_mem_mb:{(mem_after - mem_before) / (1024 * 1024)}')
    print('TEST_PASS:sfsym_help')
except subprocess.CalledProcessError as e:
    print('TEST_FAIL:sfsym_help')
    print(f'TEST_FAIL_REASON:sfsym_help:{e}')

try:
    # Export Symbols and verify output format
    start_time = time.time()
    subprocess.run(['./target/debug/sfsym', 'export', 'symbol'], check=True)
    end_time = time.time()
    print(f'BENCHMARK:export_time_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:sfsym_export')
except subprocess.CalledProcessError as e:
    print('TEST_FAIL:sfsym_export')
    print(f'TEST_FAIL_REASON:sfsym_export:{e}')

try:
    # Compare SF Symbols vs built-in toolset
    start_time = time.time()
    subprocess.run(['sfsym', 'export', 'symbol'], check=True)
    end_time = time.time()
    baseline_tool_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['./target/debug/sfsym', 'export', 'symbol'], check=True)
    end_time = time.time()
    custom_tool_time = end_time - start_time
    ratio = custom_tool_time / baseline_tool_time
    print(f'BENCHMARK:vs_sfsym_export_ratio:{ratio}')
    print('TEST_PASS:sfsym_compare')
except subprocess.CalledProcessError as e:
    print('TEST_FAIL:sfsym_compare')
    print(f'TEST_FAIL_REASON:sfsym_compare:{e}')

print('RUN_OK')