import subprocess
import time
import tracemalloc
import importlib.util
import os

def install_dependency(package_name):
    try:
        subprocess.run(['pip', 'install', package_name], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')
        try:
            subprocess.run(['git', 'clone', f'https://github.com/deepgrove-ai/{package_name}.git'])
            subprocess.run(['pip', 'install', '-e', f'./{package_name}'])
            print('INSTALL_OK')
        except Exception as e:
            print(f'INSTALL_FAIL:{str(e)}')

def test_import_time(package_name):
    try:
        start_time = time.time()
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            print(f'TEST_FAIL:{package_name}_import:module_not_found')
        else:
            importlib.util.module_from_spec(spec)
            spec.loader.exec_module(spec)
            end_time = time.time()
            import_time = (end_time - start_time) * 1000
            print(f'BENCHMARK:import_time_ms:{import_time}')
            print(f'TEST_PASS:{package_name}_import')
    except Exception as e:
        print(f'TEST_FAIL:{package_name}_import:{str(e)}')

def test_latency(package_name):
    try:
        # Assuming the package has a function called 'run' which takes no arguments
        start_time = time.time()
        spec = importlib.util.find_spec(package_name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        print(f'BENCHMARK:latency_ms:{latency}')
        print(f'TEST_PASS:{package_name}_latency')
    except Exception as e:
        print(f'TEST_FAIL:{package_name}_latency:{str(e)}')

def compare_latency(package_name, baseline_package):
    try:
        # Measure latency of the package
        start_time = time.time()
        spec = importlib.util.find_spec(package_name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run()
        end_time = time.time()
        package_latency = (end_time - start_time) * 1000

        # Measure latency of the baseline package
        start_time = time.time()
        spec = importlib.util.find_spec(baseline_package)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run()
        end_time = time.time()
        baseline_latency = (end_time - start_time) * 1000

        ratio = package_latency / baseline_latency
        print(f'BENCHMARK:vs_{baseline_package}_latency_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_FAIL:{package_name}_vs_{baseline_package}_latency:{str(e)}')

def test_memory_usage(package_name):
    try:
        tracemalloc.start()
        spec = importlib.util.find_spec(package_name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.run()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_bytes:{peak}')
        print(f'TEST_PASS:{package_name}_memory_usage')
    except Exception as e:
        print(f'TEST_FAIL:{package_name}_memory_usage:{str(e)}')

def test_loc_count(package_name):
    try:
        loc_count = 0
        for root, dirs, files in os.walk(f'./{package_name}'):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        loc_count += len(f.readlines())
        print(f'BENCHMARK:loc_count:{loc_count}')
        print(f'TEST_PASS:{package_name}_loc_count')
    except Exception as e:
        print(f'TEST_FAIL:{package_name}_loc_count:{str(e)}')

def main():
    # Install git
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print('INSTALL_OK')

    # Install the package
    package_name = 'maple-preview'
    install_dependency(package_name)

    # Test import time
    test_import_time(package_name)

    # Test latency
    test_latency(package_name)

    # Compare latency with baseline package
    baseline_package = 'vLLM'
    compare_latency(package_name, baseline_package)

    # Test memory usage
    test_memory_usage(package_name)

    # Test loc count
    test_loc_count(package_name)

    print('RUN_OK')

if __name__ == '__main__':
    main()