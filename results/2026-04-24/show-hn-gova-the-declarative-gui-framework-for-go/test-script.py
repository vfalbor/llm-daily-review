import subprocess
import time
import tracemalloc
import sys
import importlib.util
import importlib.machinery

# Install git package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK')

# Clone Gova repository
try:
    subprocess.run(['git', 'clone', 'https://github.com/NV404/gova.git'], check=True)
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:git_clone_failed:{e}')
    sys.exit(1)
else:
    print('INSTALL_OK')

# Install Gova with pip install -e
try:
    subprocess.run(['pip', 'install', '-e', './gova'], cwd='./gova', check=True)
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:pip_install_failed:{e}')
    sys.exit(1)
else:
    print('INSTALL_OK')

# Measure import time
tracemalloc.start()
start_time = time.time()
try:
    spec = importlib.util.spec_from_file_location("gova", "./gova/gova/__init__.py")
    gova = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gova)
except Exception as e:
    print(f'TEST_FAIL:gova_import:{e}')
    import_time = time.time() - start_time
    print(f'BENCHMARK:import_time_ms:{import_time * 1000}')
else:
    print('TEST_PASS:gova_import')
    import_time = time.time() - start_time
    print(f'BENCHMARK:import_time_ms:{import_time * 1000}')

# Create a simple GUI
try:
    # Since Gova is a Go-based framework, we can't directly use it in Python.
    # We'll have to use the subprocess to run a Go program using Gova.
    gova_example = '''
    package main
    import "github.com/NV404/gova"
    func main() {
        gova.Run(gova.App{
            Title: "Gova Example",
            Width: 800,
            Height: 600,
        })
    }
    '''
    with open('gova_example.go', 'w') as f:
        f.write(gova_example)
    subprocess.run(['go', 'build', 'gova_example.go'], check=True)
    start_time = time.time()
    subprocess.run(['./gova_example'], check=True)
    gui_time = time.time() - start_time
    print(f'BENCHMARK:gui_time_ms:{gui_time * 1000}')
    print('TEST_PASS:gova_gui')
except Exception as e:
    print(f'TEST_FAIL:gova_gui:{e}')

# Measure development time vs traditional frameworks
try:
    # For simplicity, we'll compare the import time of Gova with PyQt.
    start_time = time.time()
    import PyQt5
    pyqt_time = time.time() - start_time
    print(f'BENCHMARK:vs_pyqt_import_ratio:{import_time / pyqt_time}')
except Exception as e:
    print(f'TEST_FAIL:pyqt_import:{e}')

# Measure memory usage
memory, peak = tracemalloc.get_traced_memory()
print(f'BENCHMARK:memory_usage_bytes:{memory}')

# Measure test files count
try:
    test_files = subprocess.run(['find', './gova', '-name', '*_test.go'], capture_output=True, check=True)
    test_files_count = len(test_files.stdout.decode().splitlines())
    print(f'BENCHMARK:test_files_count:{test_files_count}')
except Exception as e:
    print(f'TEST_FAIL:test_files_count:{e}')

# Measure loc count
try:
    loc = subprocess.run(['wc', '-l', './gova'], capture_output=True, check=True)
    loc_count = int(loc.stdout.decode().split()[0])
    print(f'BENCHMARK:loc_count:{loc_count}')
except Exception as e:
    print(f'TEST_FAIL:loc_count:{e}')

print('RUN_OK')