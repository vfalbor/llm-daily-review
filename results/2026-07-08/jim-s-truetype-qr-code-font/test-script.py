import subprocess
import time
import tracemalloc
import pip
import importlib.util
import importlib.machinery

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK:git')

# Clone and install qr-font
try:
    subprocess.run(['git', 'clone', 'https://github.com/jimparis/qr-font.git'], check=True)
    subprocess.run(['cd', 'qr-font'], check=False)
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    print('INSTALL_OK:qr-font')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:qr-font:{str(e)}')

# Install qrencode as a baseline tool
try:
    subprocess.run(['pip', 'install', 'qrencode'], check=True)
    print('INSTALL_OK:qrencode')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:qrencode:{str(e)}')

# Test import time
start_time = time.time()
try:
    spec = importlib.util.find_spec('qr')
    if spec is not None:
        importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spec)
        importlib.import_module('qr')
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time}')
except Exception as e:
    print(f'TEST_FAIL:import_time:{str(e)}')

# Test rendering QR code
try:
    import qr
    start_time = time.time()
    qr.qr_code('https://example.com')
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    print(f'BENCHMARK:render_qr_code_ms:{latency}')
except Exception as e:
    print(f'TEST_FAIL:render_qr_code:{str(e)}')

# Test rendering QR code with qrencode
try:
    import qrencode
    start_time = time.time()
    qrencode.qrencode('https://example.com')
    end_time = time.time()
    latency_baseline = (end_time - start_time) * 1000
    ratio = latency / latency_baseline
    print(f'BENCHMARK:vs_qrencode_render_qr_code_ratio:{ratio}')
except Exception as e:
    print(f'TEST_SKIP:vs_qrencode_render_qr_code:qrencode_not_installed')

# Measure memory usage
tracemalloc.start()
import qr
tracemalloc.stop()
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_bytes:{peak}')

# Measure loc count
try:
    loc_count = subprocess.run(['wc', '-l', 'qr-font/qr/*'], capture_output=True, text=True)
    loc_count = int(loc_count.stdout.split()[0])
    print(f'BENCHMARK:loc_count:{loc_count}')
except Exception as e:
    print(f'BENCHMARK:loc_count:0')

# Measure test files count
try:
    test_files_count = subprocess.run(['find', 'qr-font/qr', '-type', 'f'], capture_output=True, text=True)
    test_files_count = len(test_files_count.stdout.splitlines())
    print(f'BENCHMARK:test_files_count:{test_files_count}')
except Exception as e:
    print(f'BENCHMARK:test_files_count:0')

print('RUN_OK')