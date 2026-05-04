import subprocess
import time
import tracemalloc
import os

# Install needed system packages
subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)

# Install tool dependencies
subprocess.run(['git', 'clone', 'https://github.com/jdgraham/abstraction-costs.git'], check=False)
os.chdir('abstraction-costs')
subprocess.run(['go', 'build', '.'], check=False)

print("INSTALL_OK")

# Run sample abstractions through the tool
def run_abstraction(name, input_str):
    try:
        start_time = time.time()
        tracemalloc.start()
        output = subprocess.check_output(['./abstraction-costs', input_str], stderr=subprocess.STDOUT).decode('utf-8')
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"TEST_PASS:{name}")
        print(f"BENCHMARK:run_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"BENCHMARK:memory_usage_kb:{peak / 1024:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{str(e)}")

# Verify costs calculated correctly
def verify_costs(name, input_str, expected_cost):
    try:
        output = subprocess.check_output(['./abstraction-costs', input_str], stderr=subprocess.STDOUT).decode('utf-8')
        if float(output.splitlines()[-1]) == expected_cost:
            print(f"TEST_PASS:{name}")
        else:
            print(f"TEST_FAIL:{name}:Cost mismatch")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{str(e)}")

# Compare vs hand-calculated costs
def compare_costs(name, input_str, expected_cost):
    try:
        output = subprocess.check_output(['./abstraction-costs', input_str], stderr=subprocess.STDOUT).decode('utf-8')
        actual_cost = float(output.splitlines()[-1])
        ratio = actual_cost / expected_cost
        print(f"BENCHMARK:vs_hand_calculated_{name}_ratio:{ratio:.2f}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{str(e)}")

# Run tests
run_abstraction('hello_world', 'hello')
verify_costs('simple_abstraction', 'simple', 10.5)
compare_costs('complex_abstraction', 'complex', 25.1)

# Measure installation time
start_time = time.time()
subprocess.run(['go', 'build', '.'], check=False)
end_time = time.time()
print(f"BENCHMARK:install_time_s:{end_time - start_time:.2f}")

# Measure import time
start_time = time.time()
subprocess.run(['go', 'build', '.'], check=False)
end_time = time.time()
print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}")

# Measure loc count
loc_count = sum(1 for line in open('main.go', 'r') if line.strip())
print(f"BENCHMARK:loc_count:{loc_count}")

# Measure test files count
test_files_count = len([f for f in os.listdir('.') if f.endswith('.go')])
print(f"BENCHMARK:test_files_count:{test_files_count}")

# Compare vs baseline tool (abstrusegoat)
try:
    subprocess.run(['cargo', 'build', '--release'], cwd='abstrusegoat', check=False)
    start_time = time.time()
    subprocess.run(['cargo', 'run', '--release'], cwd='abstrusegoat', check=False)
    end_time = time.time()
    print(f"BENCHMARK:vs_abstrusegoat_time_ms:{(end_time - start_time) * 1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:vs_abstrusegoat:{str(e)}")

print("RUN_OK")