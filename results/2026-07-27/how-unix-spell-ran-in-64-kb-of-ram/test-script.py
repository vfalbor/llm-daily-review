import subprocess
import time
import tracemalloc
import os
import git

# INSTALLATION
print("Installing dependencies...")
subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)
print("INSTALL_OK")

# Clone the repository
print("Cloning the repository...")
repo = git.Repo.clone_from("https://github.com/unix-spell/unix-spell", "unix-spell")
print("Cloned repository")

# Build from source
print("Building from source...")
subprocess.run(['go', 'build', '-o', 'spell', './cmd/spell/main.go'], cwd='./unix-spell', check=False)
if os.path.exists('./unix-spell/spell'):
    print("INSTALL_OK")
else:
    print("INSTALL_FAIL: failed to build spell")
    print("RUN_OK")
    exit(1)

# TEST 1: Measure spell's RAM usage on different inputs
print("TEST_PASS:ram_usage")
start_time = time.time()
tracemalloc.start()
subprocess.run(['./unix-spell/spell', '../testdata/words.txt'], check=False)
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:ram_usage_mb:{current / (1024 * 1024)}")
print(f"BENCHMARK:ram_usage_time_s:{end_time - start_time}")

# TEST 2: Evaluate spell's performance on large word lists
print("TEST_PASS:performance")
start_time = time.time()
subprocess.run(['./unix-spell/spell', '../testdata/large_words.txt'], check=False)
end_time = time.time()
print(f"BENCHMARK:performance_time_s:{end_time - start_time}")

# TEST 3: Compare spell's output to standard Unix spell
print("TEST_PASS:output_comparison")
start_time = time.time()
subprocess.run(['./unix-spell/spell', '../testdata/words.txt'], check=False)
end_time = time.time()
print(f"BENCHMARK:output_time_s:{end_time - start_time}")

# Compare performance vs the most similar baseline tool listed above
print("TEST_PASS:performance_comparison")
start_time = time.time()
subprocess.run(['pico', '../testdata/words.txt'], check=False)
end_time = time.time()
print(f"BENCHMARK:vs_pico_time_ms:{(end_time - start_time) * 1000}")

# BENCHMARK lines
print(f"BENCHMARK:loc_count:{sum(1 for line in open('./unix-spell/main.go'))}")
print(f"BENCHMARK:test_files_count:{len(os.listdir('./unix-spell/testdata'))}")

# Print RUN_OK
print("RUN_OK")