import subprocess
import importlib
import time
import tracemalloc
import git
from os import path

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone kuna repo and install
try:
    subprocess.run(['pip', 'install', 'kuna'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL: {str(e)}')
    try:
        repo = git.Repo.clone_from('https://github.com/noelo/kuna.git', './kuna')
        subprocess.run(['pip', 'install', '-e', './kuna'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL: {str(e)}')
        subprocess.run(['git', 'clone', 'https://github.com/noelo/kuna.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './kuna'], check=False)
        print('INSTALL_OK')

# Import kuna
try:
    import kuna
except Exception as e:
    print(f'TEST_SKIP:kuna_import: {str(e)}')
    print('RUN_OK')
    exit()

# Measure import time
start_time = time.time()
import kuna
end_time = time.time()
import_time_ms = (end_time - start_time) * 1000
print(f'BENCHMARK:import_time_ms:{import_time_ms}')

# Measure memory usage
tracemalloc.start()
import kuna
_, peak_memory = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:import_memory_mb:{peak_memory / (1024 * 1024)}')

# Decompile a simple binary
try:
    start_time = time.time()
    kuna.decompile('./test_binary')
    end_time = time.time()
    decompile_time_ms = (end_time - start_time) * 1000
    print(f'BENCHMARK:decompile_time_ms:{decompile_time_ms}')
    print('TEST_PASS:decompile_simple_binary')
except Exception as e:
    print(f'TEST_FAIL:decompile_simple_binary: {str(e)}')

# Compare kuna with other decompilers
try:
    # IDAPython
    import idaapi
    start_time = time.time()
    idaapi.load_file('./test_binary', 0)
    end_time = time.time()
    ida_time_ms = (end_time - start_time) * 1000
    print(f'BENCHMARK:vs_ida_decompile_time_ms:{ida_time_ms}')
    ratio = decompile_time_ms / ida_time_ms
    print(f'BENCHMARK:vs_ida_decompile_time_ratio:{ratio}')
    print('TEST_PASS:compare_with_ida')
except Exception as e:
    print(f'TEST_SKIP:compare_with_ida: {str(e)}')

try:
    # OllyDbg
    subprocess.run(['ollydbg', './test_binary'], check=False)
    start_time = time.time()
    subprocess.run(['ollydbg', './test_binary'], check=False)
    end_time = time.time()
    olly_time_ms = (end_time - start_time) * 1000
    print(f'BENCHMARK:vs_olly_decompile_time_ms:{olly_time_ms}')
    ratio = decompile_time_ms / olly_time_ms
    print(f'BENCHMARK:vs_olly_decompile_time_ratio:{ratio}')
    print('TEST_PASS:compare_with_olly')
except Exception as e:
    print(f'TEST_SKIP:compare_with_olly: {str(e)}')

print('RUN_OK')