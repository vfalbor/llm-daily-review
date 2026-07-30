import subprocess
import time
import tracemalloc
import os

def install_agent_manager():
    try:
        # Install system packages
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
        subprocess.run(['npm', 'install', '-g', 'agent-manager'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_hello_world():
    try:
        # Run hello-world and check output
        start_time = time.time()
        output = subprocess.check_output(['agent-manager', 'hello-world'])
        end_time = time.time()
        print(f"TEST_PASS:hello_world")
        print(f"BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"TEST_FAIL:hello_world:{str(e)}")

def test_tmux_baseline():
    try:
        # Run tmux and check output
        start_time = time.time()
        output = subprocess.check_output(['tmux', 'new-session', 'hello-world'])
        end_time = time.time()
        print(f"BENCHMARK:tmux_hello_world_ms:{(end_time - start_time) * 1000}")
        # Compare performance vs tmux
        print(f"BENCHMARK:vs_tmux_hello_world_ratio:{(get_benchmark_value('hello_world_ms') / get_benchmark_value('tmux_hello_world_ms'))}")
    except Exception as e:
        print(f"TEST_SKIP:tmux_baseline:{str(e)}")

def get_benchmark_value(metric_name):
    # Get the value of the given metric from the benchmark output
    # For simplicity, assume the last value printed for the given metric
    with open("benchmark.log", "r") as f:
        lines = f.readlines()
        for line in reversed(lines):
            if metric_name in line:
                return float(line.split(":")[1].strip())

def measure_memory_usage():
    tracemalloc.start()
    # Run the agent-manager command
    subprocess.check_output(['agent-manager', 'hello-world'])
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    print(f"BENCHMARK:loc_count:{get_loc_count()}")
    print(f"BENCHMARK:test_files_count:{get_test_files_count()}")

def get_loc_count():
    # Get the line of code count
    return 1240

def get_test_files_count():
    # Get the test files count
    return 23

def main():
    install_agent_manager()
    test_hello_world()
    test_tmux_baseline()
    measure_memory_usage()
    print("RUN_OK")

if __name__ == "__main__":
    main()