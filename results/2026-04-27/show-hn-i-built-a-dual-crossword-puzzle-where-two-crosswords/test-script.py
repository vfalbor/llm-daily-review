import subprocess
import time
import tracemalloc
import importlib.util
import sys

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['pip', 'install', 'forkle'], check=False)

def import_module(module_name):
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        return None
    return importlib.util.module_from_spec(spec)

def generate_puzzle(module):
    puzzle = module.generate_puzzle()
    return puzzle

def test_puzzle_solvable(puzzle):
    try:
        solution = puzzle.solve()
        return True
    except Exception as e:
        print(f"TEST_FAIL:solve_puzzle:{str(e)}")
        return False

def measure_import_time(module_name):
    start_time = time.time()
    importlib.import_module(module_name)
    end_time = time.time()
    return (end_time - start_time) * 1000

def measure_operation_latency(module_name, operation):
    start_time = time.time()
    importlib.import_module(module_name)
    module = importlib.import_module(module_name)
    operation(module)
    end_time = time.time()
    return (end_time - start_time) * 1000

def compare_to_baseline(module_name):
    try:
        import baseline
        baseline_module = baseline
        start_time = time.time()
        baseline_module.solve_puzzle()
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        start_time = time.time()
        importlib.import_module(module_name).solve_puzzle()
        end_time = time.time()
        module_time = (end_time - start_time) * 1000
        ratio = module_time / baseline_time
        return ratio
    except ImportError:
        return None

def main():
    try:
        install_dependencies()
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")
        return

    try:
        module_name = 'forkle'
        start_time = time.time()
        importlib.import_module(module_name)
        end_time = time.time()
        import_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:import_time_ms:{import_time}")
    except ImportError as e:
        print(f"INSTALL_FAIL:{str(e)}")
        return

    try:
        module = importlib.import_module(module_name)
        puzzle = module.generate_puzzle()
        print(f"TEST_PASS:generate_puzzle")
        start_time = time.time()
        puzzle.solve()
        end_time = time.time()
        operation_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:solve_puzzle_ms:{operation_latency}")
        if test_puzzle_solvable(puzzle):
            print(f"TEST_PASS:solve_puzzle")
        else:
            print(f"TEST_FAIL:solve_puzzle:failed to solve")
    except Exception as e:
        print(f"TEST_FAIL:solve_puzzle:{str(e)}")

    try:
        ratio = compare_to_baseline(module_name)
        if ratio is not None:
            print(f"BENCHMARK:vs_baseline_time_ratio:{ratio}")
        else:
            print(f"TEST_SKIP:baseline_comparison:baseline module not found")
    except Exception as e:
        print(f"TEST_FAIL:baseline_comparison:{str(e)}")

    try:
        tracemalloc.start()
        importlib.import_module(module_name).solve_puzzle()
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024)}")
        tracemalloc.stop()
    except Exception as e:
        print(f"TEST_FAIL:memory_usage:{str(e)}")

    try:
        start_time = time.time()
        importlib.import_module(module_name).generate_puzzle()
        end_time = time.time()
        operation_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:generate_puzzle_ms:{operation_latency}")
    except Exception as e:
        print(f"TEST_FAIL:generate_puzzle:{str(e)}")

    try:
        num_tests = 10
        start_time = time.time()
        for _ in range(num_tests):
            importlib.import_module(module_name).solve_puzzle()
        end_time = time.time()
        operation_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:batch_solve_puzzle_ms:{operation_latency / num_tests}")
    except Exception as e:
        print(f"TEST_FAIL:batch_solve_puzzle:{str(e)}")

    try:
        num_tests = 10
        start_time = time.time()
        for _ in range(num_tests):
            importlib.import_module(module_name).generate_puzzle()
        end_time = time.time()
        operation_latency = (end_time - start_time) * 1000
        print(f"BENCHMARK:batch_generate_puzzle_ms:{operation_latency / num_tests}")
    except Exception as e:
        print(f"TEST_FAIL:batch_generate_puzzle:{str(e)}")

    print("RUN_OK")

if __name__ == "__main__":
    main()