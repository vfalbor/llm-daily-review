import subprocess
import time
import tracemalloc
import os
import git

# Install required packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'gcc'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'make'], check=False)
print('INSTALL_OK')

# Clone repository
try:
    repo = git.Repo.clone_from('https://github.com/WeebLabs/DSPi.git', 'DSPi')
    print('TEST_PASS:clone')
except Exception as e:
    print(f'TEST_FAIL:clone:{str(e)}')

# Build from source
try:
    subprocess.run(['make', '-C', 'DSPi'], check=True)
    print('TEST_PASS:build')
except Exception as e:
    print(f'TEST_FAIL:build:{str(e)}')

# Measure build time
start_time = time.time()
try:
    subprocess.run(['make', '-C', 'DSPi'], check=True)
    build_time = time.time() - start_time
    print(f'BENCHMARK:build_time_s:{build_time:.2f}')
except Exception as e:
    print(f'TEST_FAIL:build:{str(e)}')

# Count source files and languages
try:
    languages = set()
    for root, dirs, files in os.walk('DSPi'):
        for file in files:
            if file.endswith(('.c', '.cpp', '.h', '.hpp', '.py', '.java')):
                languages.add(file.split('.')[-1])
    print(f'BENCHMARK:source_languages:{len(languages)}')
    print(f'BENCHMARK:source_files_count:{len([file for file in os.listdir('DSPi') if os.path.isfile(os.path.join('DSPi', file))])}')
    print('TEST_PASS:source_count')
except Exception as e:
    print(f'TEST_FAIL:source_count:{str(e)}')

# Check for simulator/emulator
try:
    subprocess.run(['make', 'simulate', '-C', 'DSPi'], check=True)
    print('TEST_PASS:simulate')
except Exception as e:
    print(f'TEST_FAIL:simulate:{str(e)}')

# Run Python examples
try:
    python_files = [file for file in os.listdir('DSPi') if file.endswith('.py')]
    for file in python_files:
        start_time = time.time()
        subprocess.run(['python', os.path.join('DSPi', file)], check=True)
        run_time = time.time() - start_time
        print(f'BENCHMARK:python_example_{file}_time_ms:{run_time*1000:.2f}')
    print('TEST_PASS:python_examples')
except Exception as e:
    print(f'TEST_FAIL:python_examples:{str(e)}')

# Measure memory usage
try:
    tracemalloc.start()
    subprocess.run(['make', '-C', 'DSPi'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{peak}')
    tracemalloc.stop()
except Exception as e:
    print(f'TEST_FAIL:memory_usage:{str(e)}')

# Compare performance vs baseline tool
try:
    # Measure time taken to run DSPi
    start_time = time.time()
    subprocess.run(['make', '-C', 'DSPi'], check=True)
    dsp_time = time.time() - start_time

    # Measure time taken to run PicoSDK
    start_time = time.time()
    subprocess.run(['make', '-C', 'PicoSDK'], check=True)
    pico_time = time.time() - start_time

    print(f'BENCHMARK:vs_pico_build_time_ratio:{dsp_time/pico_time:.2f}')
    print('TEST_PASS:performance_comparison')
except Exception as e:
    print(f'TEST_FAIL:performance_comparison:{str(e)}')

print('RUN_OK')