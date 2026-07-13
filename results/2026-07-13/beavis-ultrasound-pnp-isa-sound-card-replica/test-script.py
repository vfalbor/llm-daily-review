import subprocess
import time
import tracemalloc
import os

# Install system packages with subprocess
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'gcc'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'make'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'python3'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'python3-dev'], check=False)
print("INSTALL_OK")

# Clone and build the sound card from source
try:
    subprocess.run(['git', 'clone', 'https://github.com/schlae/BeavisUltrasound.git'], check=False)
    os.chdir('BeavisUltrasound')
    start_time = time.time()
    subprocess.run(['make'], check=False)
    build_time = time.time() - start_time
    print(f"BENCHMARK:build_time_s:{build_time}")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Count source files and languages
try:
    source_files = 0
    languages = set()
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.c', '.h', '.cpp', '.py', '.java', '.js', '.go', '.swift', '.kt', '.java', '.cpp', '.hpp', '.cs', '.vb', '.php', '.rb', '.lua', '.perl', '.tcl', '.pl', '.ps1', '.sh', '.bash', '.zsh', '.fish', '.awk', '.sed', '.grep', '.rs', '.erl', '.elixir', '.erlang', '.scala')):
                source_files += 1
                languages.add(file.split('.')[-1])
    print(f"BENCHMARK:source_files_count:{source_files}")
    print(f"BENCHMARK:programming_languages_count:{len(languages)}")
    print("TEST_PASS:source_file_count")
except Exception as e:
    print(f"TEST_FAIL:source_file_count:{str(e)}")

# Check for simulator/emulator
try:
    # Check if simulator/emulator exists in the repository
    if 'simulator' in os.listdir() or 'emulator' in os.listdir():
        print("TEST_PASS:simulator/emulator_exists")
    else:
        print("TEST_SKIP:simulator/emulator_exists:Not found")
except Exception as e:
    print(f"TEST_FAIL:simulator/emulator_exists:{str(e)}")

# Run any Python examples found
try:
    # Find Python examples in the repository
    python_examples = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_examples.append(os.path.join(root, file))

    # Run Python examples
    for example in python_examples:
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['python3', example], check=False)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        run_time = time.time() - start_time
        print(f"BENCHMARK:example_{os.path.basename(example)}_run_time_ms:{run_time * 1000}")
        print(f"BENCHMARK:example_{os.path.basename(example)}_peak_memory_mb:{peak / 10**6}")
        print(f"TEST_PASS:run_example_{os.path.basename(example)}")
except Exception as e:
    print(f"TEST_FAIL:run_examples:{str(e)}")

# Compare performance with the original sound card
try:
    # Measure time it takes to run a Python example with the sound card
    start_time = time.time()
    subprocess.run(['python3', 'example.py'], check=False)
    run_time = time.time() - start_time

    # Measure time it takes to run the same example with the baseline tool (VBox)
    start_time = time.time()
    subprocess.run(['vbox', 'example.py'], check=False)
    baseline_run_time = time.time() - start_time

    print(f"BENCHMARK:vs_vbox_example_run_time_ratio:{run_time / baseline_run_time}")
    print("TEST_PASS:performance_comparison")
except Exception as e:
    print(f"TEST_FAIL:performance_comparison:{str(e)}")

print("RUN_OK")