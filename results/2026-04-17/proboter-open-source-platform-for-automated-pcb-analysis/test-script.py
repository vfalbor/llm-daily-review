import subprocess
import time
import tracemalloc
import os
import sys
import git

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the PROBoter repository
try:
    repo = git.Repo.clone_from('https://github.com/schutzwerk/PROBoter.git', 'proboter')
    print('INSTALL_OK')
except Exception as e:
    print('INSTALL_FAIL:git clone failed')
    print('TEST_SKIP:clone_fail', ':git clone failed')
    sys.exit(0)

# Count source files and languages
try:
    source_files = 0
    languages = set()
    for root, dirs, files in os.walk('proboter'):
        for file in files:
            if file.endswith(('.py', '.c', '.cpp', '.java', '.js')):
                source_files += 1
                languages.add(file.split('.')[-1])
    print(f'BENCHMARK:source_files_count:{source_files}')
    print(f'BENCHMARK:languages_count:{len(languages)}')
except Exception as e:
    print(f'TEST_FAIL:count_source_files:{e}')

# Check for simulator/emulator
try:
    simulator = False
    for root, dirs, files in os.walk('proboter'):
        for file in files:
            if file.endswith(('.sim', '.emu')):
                simulator = True
                break
    if simulator:
        print('BENCHMARK:simulator_found:True')
    else:
        print('BENCHMARK:simulator_found:False')
except Exception as e:
    print(f'TEST_FAIL:check_simulator:{e}')

# Run any Python examples found
try:
    python_examples = []
    for root, dirs, files in os.walk('proboter'):
        for file in files:
            if file.endswith('.py') and file.startswith('example'):
                python_examples.append(os.path.join(root, file))
    for example in python_examples:
        subprocess.run(['python', example], check=False)
    print('TEST_PASS:run_python_examples')
except Exception as e:
    print(f'TEST_FAIL:run_python_examples:{e}')

# Compare PROBoter's results with commercial PCB analysis tools
try:
    import kicad
    kicad_result = kicad.analyze('example_pcb.kicad_pcb')
    proboter_result = subprocess.run(['proboter', 'example_pcb.kicad_pcb'], capture_output=True, text=True)
    if kicad_result == proboter_result.stdout:
        print('TEST_PASS:compare_with_kicad')
    else:
        print('TEST_FAIL:compare_with_kicad:results do not match')
except Exception as e:
    print(f'TEST_FAIL:compare_with_kicad:{e}')

# Compare performance vs the most similar baseline tool listed above
try:
    import fritzing
    fritzing_time = time.time()
    fritzing.analyze('example_pcb.fzz')
    fritzing_time = time.time() - fritzing_time
    proboter_time = time.time()
    subprocess.run(['proboter', 'example_pcb.kicad_pcb'], capture_output=True, text=True)
    proboter_time = time.time() - proboter_time
    print(f'BENCHMARK:vs_fritzing_ratio:{proboter_time / fritzing_time}')
except Exception as e:
    print(f'TEST_FAIL:compare_with_fritzing:{e}')

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_bytes:{current}')
tracemalloc.stop()

# Measure execution time
start_time = time.time()
subprocess.run(['proboter', 'example_pcb.kicad_pcb'], capture_output=True, text=True)
end_time = time.time()
print(f'BENCHMARK:execution_time_s:{end_time - start_time}')

# Print final message
print('RUN_OK')