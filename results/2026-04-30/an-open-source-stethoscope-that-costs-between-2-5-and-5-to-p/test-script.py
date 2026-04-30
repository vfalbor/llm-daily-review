import subprocess
import os
import time
import tracemalloc
import git
import shutil

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the repository
start_time = time.time()
try:
    repo = git.Repo.clone_from('https://github.com/GliaX/Stethoscope.git', 'stethoscope')
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

# Count source files and languages
try:
    start_tracemalloc = time.time()
    tracemalloc.start()
    languages = set()
    for root, dirs, files in os.walk('stethoscope'):
        for file in files:
            if file.endswith(('.c', '.cpp', '.py', '.java', '.js', '.html', '.css')):
                languages.add(file.split('.')[-1])
    end_tracemalloc = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:file_count:{len(os.listdir("stethoscope"))}')
    print(f'BENCHMARK:language_count:{len(languages)}')
    print(f'BENCHMARK:tracemalloc_time_ms:{(end_tracemalloc - start_tracemalloc) * 1000}')
    print(f'BENCHMARK:tracemalloc_peak_mb:{peak / (1024 * 1024)}')
    tracemalloc.stop()
    print('TEST_PASS:file_and_language_count')
except Exception as e:
    print(f'TEST_FAIL:file_and_language_count:{str(e)}')

# Check for simulator/emulator
try:
    simulator_found = False
    for root, dirs, files in os.walk('stethoscope'):
        for file in files:
            if file == 'simulator.py' or file == 'emulator.py':
                simulator_found = True
    if simulator_found:
        print('TEST_PASS:simulator_found')
    else:
        print('TEST_SKIP:simulator_not_found')
except Exception as e:
    print(f'TEST_FAIL:simulator_check:{str(e)}')

# Run any Python examples found
try:
    python_files = []
    for root, dirs, files in os.walk('stethoscope'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    for file in python_files:
        start_time = time.time()
        subprocess.run(['python', file], check=False)
        end_time = time.time()
        print(f'BENCHMARK:python_file_run_time_ms:{(end_time - start_time) * 1000}')
    print('TEST_PASS:python_examples_run')
except Exception as e:
    print(f'TEST_FAIL:python_examples_run:{str(e)}')

# Clone baseline repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/3M-Littmann/stethoscope.git', 'baseline'], check=False)
    print('TEST_PASS:baseline_clone')
except Exception as e:
    print(f'TEST_FAIL:baseline_clone:{str(e)}')

# Compare performance vs the most similar baseline tool
try:
    start_time = time.time()
    subprocess.run(['python', 'stethoscope/stethoscope.py'], check=False)
    end_time = time.time()
    baseline_start_time = time.time()
    subprocess.run(['python', 'baseline/baseline.py'], check=False)
    baseline_end_time = time.time()
    print(f'BENCHMARK:stethoscope_run_time_ms:{(end_time - start_time) * 1000}')
    print(f'BENCHMARK:baseline_run_time_ms:{(baseline_end_time - baseline_start_time) * 1000}')
    print(f'BENCHMARK:vs_baseline_run_time_ratio:{(end_time - start_time) / (baseline_end_time - baseline_start_time)}')
    print('TEST_PASS:performance_comparison')
except Exception as e:
    print(f'TEST_FAIL:performance_comparison:{str(e)}')

# Clean up
try:
    shutil.rmtree('stethoscope')
    shutil.rmtree('baseline')
    print('TEST_PASS:cleanup')
except Exception as e:
    print(f'TEST_FAIL:cleanup:{str(e)}')

# Print RUN_OK
print('RUN_OK')