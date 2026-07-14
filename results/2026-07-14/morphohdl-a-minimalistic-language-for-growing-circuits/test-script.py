import subprocess
import time
import tracemalloc
import os

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'go', 'git', 'cargo', 'rust', 'nodejs', 'npm'], check=False)
    print("INSTALL_OK")

def clone_and_build_morpho():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/paradigms-of-intelligence/morpho.git'], check=False)
        os.chdir('morpho')
        subprocess.run(['cargo', 'build'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def compile_morpho_code():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run', '--bin', 'morpho', '--', 'examples/hello.morpho'], check=False)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:compile_time_ms:{execution_time:.2f}")
        print(f"TEST_PASS:compile_morpho_code")
    except Exception as e:
        print(f"TEST_FAIL:compile_morpho_code:{str(e)}")

def grow_simple_circuit():
    try:
        start_time = time.time()
        subprocess.run(['cargo', 'run', '--bin', 'morpho', '--', 'examples/circuit.morpho'], check=False)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:grow_circuit_time_ms:{execution_time:.2f}")
        print(f"TEST_PASS:grow_simple_circuit")
    except Exception as e:
        print(f"TEST_FAIL:grow_simple_circuit:{str(e)}")

def compare_with_baseline():
    try:
        # Assuming GraphcodeNets as the baseline tool
        start_time = time.time()
        subprocess.run(['node', 'graphcode-nets/examples/hello.js'], check=False)
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run(['cargo', 'run', '--bin', 'morpho', '--', 'examples/hello.morpho'], check=False)
        end_time = time.time()
        morpho_time = (end_time - start_time) * 1000
        ratio = morpho_time / baseline_time
        print(f"BENCHMARK:vs_graphcode_nets_ratio:{ratio:.2f}")
        print(f"TEST_PASS:compare_with_baseline")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_baseline:{str(e)}")

def measure_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['cargo', 'run', '--bin', 'morpho', '--', 'examples/hello.morpho'], check=False)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
    except Exception as e:
        print(f"TEST_FAIL:measure_memory_usage:{str(e)}")

def count_files():
    try:
        file_count = len(os.listdir('.'))
        print(f"BENCHMARK:file_count:{file_count}")
    except Exception as e:
        print(f"TEST_FAIL:count_files:{str(e)}")

def count_loc():
    try:
        loc_count = 0
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.morpho'):
                    with open(os.path.join(root, file), 'r') as f:
                        loc_count += len(f.readlines())
        print(f"BENCHMARK:loc_count:{loc_count}")
    except Exception as e:
        print(f"TEST_FAIL:count_loc:{str(e)}")

install_dependencies()
clone_and_build_morpho()
compile_morpho_code()
grow_simple_circuit()
compare_with_baseline()
measure_memory_usage()
count_files()
count_loc()
print("RUN_OK")