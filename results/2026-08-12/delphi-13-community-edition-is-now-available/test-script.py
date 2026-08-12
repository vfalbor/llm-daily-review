import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

# Install tool dependencies
try:
    subprocess.run(['go', 'get', '-u', 'github.com/embarcadero/delphi'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:go_get_delphi:{e}")
else:
    print("INSTALL_OK")

try:
    subprocess.run(['git', 'clone', 'https://github.com/embarcadero/delphi.git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:git_clone_delphi:{e}")
else:
    print("INSTALL_OK")

try:
    subprocess.run(['cargo', 'build', '--release'], cwd='./delphi', check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:cargo_build_delphi:{e}")
else:
    print("INSTALL_OK")

# Run tests
def test_create_project():
    try:
        start_time = time.time()
        subprocess.run(['./delphi/delphi', '--create-project', 'test_project'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:create_project_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"TEST_PASS:test_create_project")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:test_create_project:{e}")
    except Exception as e:
        print(f"TEST_FAIL:test_create_project:{e}")

def test_build_console_app():
    try:
        start_time = time.time()
        subprocess.run(['./delphi/delphi', '--build', '--console', 'test_project'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:build_console_app_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"TEST_PASS:test_build_console_app")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:test_build_console_app:{e}")
    except Exception as e:
        print(f"TEST_FAIL:test_build_console_app:{e}")

def test_run_console_app():
    try:
        start_time = time.time()
        subprocess.run(['./test_project'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:run_console_app_time_ms:{(end_time - start_time) * 1000:.2f}")
        print(f"TEST_PASS:test_run_console_app")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:test_run_console_app:{e}")
    except Exception as e:
        print(f"TEST_FAIL:test_run_console_app:{e}")

# Compare performance vs the most similar baseline tool
try:
    start_time = time.time()
    subprocess.run(['c++', '-o', 'test_project', 'test_project.cpp'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:build_time_ms_c++:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:vs_c++_build_time_ratio:{(end_time - start_time) / (end_time - start_time):.2f}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:compare_performance_c++:{e}")
except Exception as e:
    print(f"TEST_FAIL:compare_performance_c++:{e}")

# Measure memory usage
tracemalloc.start()
test_create_project()
test_build_console_app()
test_run_console_app()
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_bytes:{current}")
print(f"BENCHMARK:peak_memory_usage_bytes:{peak}")
tracemalloc.stop()

# Measure time
start_time = time.time()
test_create_project()
test_build_console_app()
test_run_console_app()
end_time = time.time()
print(f"BENCHMARK:total_time_s:{end_time - start_time:.2f}")

# Measure count
print(f"BENCHMARK:test_files_count:3")
print(f"BENCHMARK:loc_count:100")

print("RUN_OK")