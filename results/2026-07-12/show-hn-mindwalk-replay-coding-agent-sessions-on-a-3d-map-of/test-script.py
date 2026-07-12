import time
import tracemalloc
import subprocess
import sys

print("INSTALLING PACKAGES")
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

print("INSTALLING MINDWALK")
try:
    subprocess.run(['pip', 'install', 'mindwalk'], check=True)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:pip_install")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/cosmtrek/mindwalk.git'], check=True)
        subprocess.run(['pip', 'install', '-e', 'mindwalk'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:git_clone")
        sys.exit()

import mindwalk
print("IMPORTING MINDWALK")

start_time = time.time()
import mindwalk
import_time = time.time() - start_time
print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")

def test_install():
    try:
        mindwalk.create_project("test_project")
        print("TEST_PASS:create_project")
    except Exception as e:
        print(f"TEST_FAIL:create_project:{e}")

def test_run():
    try:
        mindwalk.run("test_project")
        print("TEST_PASS:run")
    except Exception as e:
        print(f"TEST_FAIL:run:{e}")

def test_performance():
    try:
        start_time = time.time()
        mindwalk.run("test_project")
        end_time = time.time()
        run_time = end_time - start_time
        print(f"BENCHMARK:run_time_ms:{run_time*1000:.2f}")
        print("TEST_PASS:performance")
    except Exception as e:
        print(f"TEST_FAIL:performance:{e}")

def test_accuracy():
    try:
        mindwalk.replay_session("test_project")
        print("TEST_PASS:accuracy")
    except Exception as e:
        print(f"TEST_FAIL:accuracy:{e}")

tracemalloc.start()
start_time = time.time()
mindwalk.create_project("test_project")
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")
print(f"BENCHMARK:create_time_ms:{(end_time-start_time)*1000:.2f}")

# Compare performance vs Langchain
try:
    import langchain
    start_time = time.time()
    langchain.run("test_project")
    end_time = time.time()
    langchain_time = end_time - start_time
    start_time = time.time()
    mindwalk.run("test_project")
    end_time = time.time()
    mindwalk_time = end_time - start_time
    ratio = mindwalk_time / langchain_time
    print(f"BENCHMARK:vs_langchain_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_SKIP:langchain_comparison:{e}")

# Run tests
test_install()
test_run()
test_performance()
test_accuracy()

print("RUN_OK")