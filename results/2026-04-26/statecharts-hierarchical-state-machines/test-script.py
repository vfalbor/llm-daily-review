import subprocess
import sys
import importlib.util
import importlib.machinery
import time
import tracemalloc
import json
import os

# Install system package with apk
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
except subprocess.CalledProcessError as e:
    print('INSTALL_FAIL:failed to install git')
    sys.exit(1)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'statecharts'], check=True)
except subprocess.CalledProcessError as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/statecharts/statecharts.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './statecharts'], check=True)
    except subprocess.CalledProcessError as e:
        print('INSTALL_FAIL:failed to install statecharts')
        sys.exit(1)

# Print installation status
print('INSTALL_OK')

# Load the statecharts library
spec = importlib.util.find_spec('statecharts')
if spec is None:
    print('TEST_FAIL:load_statecharts:library not found')
else:
    try:
        statecharts = importlib.import_module('statecharts')
        print('TEST_PASS:load_statecharts')
    except Exception as e:
        print(f'TEST_FAIL:load_statecharts:{e}')

# Create a machine and add a single transition
try:
    machine = statecharts.Machine({
        'id': 'example',
        'initial': 'active',
        'states': {
            'active': {
                'on': {
                    'toggle': 'inactive'
                }
            },
            'inactive': {
                'on': {
                    'toggle': 'active'
                }
            }
        }
    })
    machine.transition('toggle')
    print('TEST_PASS:create_machine')
except Exception as e:
    print(f'TEST_FAIL:create_machine:{e}')

# Create a complex machine and verify that it compiles without errors
try:
    complex_machine = statecharts.Machine({
        'id': 'complex',
        'initial': 'active',
        'states': {
            'active': {
                'on': {
                    'toggle': 'inactive',
                    'deepen': 'nested'
                }
            },
            'inactive': {
                'on': {
                    'toggle': 'active'
                }
            },
            'nested': {
                'initial': 'inner',
                'states': {
                    'inner': {
                        'on': {
                            'exit': 'active'
                        }
                    }
                }
            }
        }
    })
    print('TEST_PASS:create_complex_machine')
except Exception as e:
    print(f'TEST_FAIL:create_complex_machine:{e}')

# Measure import time
import_time_start = time.time()
importlib.import_module('statecharts')
import_time_end = time.time()
import_time = import_time_end - import_time_start
print(f'BENCHMARK:import_time_ms:{import_time * 1000}')

# Measure core operation latency
try:
    tracemalloc.start()
    statecharts.Machine({
        'id': 'example',
        'initial': 'active',
        'states': {
            'active': {
                'on': {
                    'toggle': 'inactive'
                }
            },
            'inactive': {
                'on': {
                    'toggle': 'active'
                }
            }
        }
    })
    latency_start = time.time()
    for _ in range(1000):
        statecharts.Machine({
            'id': 'example',
            'initial': 'active',
            'states': {
                'active': {
                    'on': {
                        'toggle': 'inactive'
                    }
                },
                'inactive': {
                    'on': {
                        'toggle': 'active'
                    }
                }
            }
        })
    latency_end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    latency = latency_end - latency_start
    print(f'BENCHMARK:core_operation_latency_ms:{latency * 1000}')
    print(f'BENCHMARK:core_operation_memory_mb:{current / 1024 / 1024}')
except Exception as e:
    print(f'TEST_FAIL:measure_core_operation_latency:{e}')

# Compare performance against a traditional state machine implementation
try:
    class TraditionalStateMachine:
        def __init__(self):
            self.state = 'active'

        def transition(self):
            if self.state == 'active':
                self.state = 'inactive'
            else:
                self.state = 'active'

    traditional_state_machine = TraditionalStateMachine()
    traditional_latency_start = time.time()
    for _ in range(1000):
        traditional_state_machine.transition()
    traditional_latency_end = time.time()
    traditional_latency = traditional_latency_end - traditional_latency_start
    ratio = latency / traditional_latency
    print(f'BENCHMARK:vs_traditional_core_operation_latency_ratio:{ratio}')
except Exception as e:
    print(f'TEST_FAIL:compare_performance:{e}')

# Measure execution time of a demo app
try:
    exec_time_start = time.time()
    with open('statecharts/demo.py', 'r') as f:
        code = f.read()
    exec(code)
    exec_time_end = time.time()
    exec_time = exec_time_end - exec_time_start
    print(f'BENCHMARK:demo_app_execution_time_ms:{exec_time * 1000}')
except Exception as e:
    print(f'TEST_FAIL:measure_demo_app_execution_time:{e}')

# Count lines of code
try:
    loc_count = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += sum(1 for line in f if line.strip())
    print(f'BENCHMARK:loc_count:{loc_count}')
except Exception as e:
    print(f'TEST_FAIL:count_loc:{e}')

# Count test files
try:
    test_files_count = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('_test.py'):
                test_files_count += 1
    print(f'BENCHMARK:test_files_count:{test_files_count}')
except Exception as e:
    print(f'TEST_FAIL:count_test_files:{e}')

print('RUN_OK')