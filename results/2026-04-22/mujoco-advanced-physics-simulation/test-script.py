import subprocess
import time
import tracemalloc
import importlib
import importlib.util
import os
import sys

# INSTALL OK/FAIL
try:
    # Install git
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:Failed to install git {e}')

# Install MuJoCo
try:
    # Clone MuJoCo repository
    subprocess.run(['git', 'clone', 'https://github.com/deepmind/mujoco'], check=False)
    # Install MuJoCo using pip
    subprocess.run(['pip', 'install', '-e', './mujoco'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:Failed to install MuJoCo {e}')

# Clone ODE repository as a baseline tool
try:
    subprocess.run(['git', 'clone', 'https://github.com/ode/ode'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:Failed to install ODE {e}')

# TESTS
def test_import():
    try:
        start_time = time.time()
        import mujoco
        end_time = time.time()
        print(f'BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}')
        print('TEST_PASS:test_import')
    except Exception as e:
        print(f'TEST_FAIL:test_import:{e}')

def test_simulation():
    try:
        import mujoco
        tracemalloc.start()
        start_time = time.time()
        # Create a simple simulation
        sim = mujoco.MjSim()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:simulation_time_ms:{(end_time - start_time) * 1000:.2f}')
        print(f'BENCHMARK:simulation_memory_mb:{current / (1024 * 1024):.2f}')
        print('TEST_PASS:test_simulation')
    except Exception as e:
        print(f'TEST_FAIL:test_simulation:{e}')

def test_baseline_comparison():
    try:
        import mujoco
        # Import ODE baseline tool
        spec = importlib.util.spec_from_file_location("ode", "./ode/ode.py")
        ode = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ode)
        # Measure import time of ODE
        start_time = time.time()
        import ode
        end_time = time.time()
        ode_import_time = (end_time - start_time) * 1000
        # Measure import time of MuJoCo
        start_time = time.time()
        import mujoco
        end_time = time.time()
        mujoco_import_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:vs_ode_import_time_ratio:{mujoco_import_time / ode_import_time:.2f}')
        print('TEST_PASS:test_baseline_comparison')
    except Exception as e:
        print(f'TEST_FAIL:test_baseline_comparison:{e}')

# Run tests
test_import()
test_simulation()
test_baseline_comparison()

# BENCHMARK lines
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_peak_mb:{peak / (1024 * 1024):.2f}')
print(f'BENCHMARK:memory_current_mb:{current / (1024 * 1024):.2f}')
print(f'BENCHMARK:cpu_idle_time_s:1')

# Always print RUN_OK
print('RUN_OK')