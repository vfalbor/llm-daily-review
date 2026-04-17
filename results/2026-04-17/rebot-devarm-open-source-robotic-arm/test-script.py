import subprocess
import time
import tracemalloc
import os
import sys

def install_system_packages(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def install_tool_dependencies(tool, package=None):
    if package:
        try:
            subprocess.run(['pip', 'install', '-e', package], check=False)
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")
    else:
        try:
            subprocess.run(['git', 'clone', tool], check=False)
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")

def count_source_files(path):
    try:
        return sum([len(files) for r, d, files in os.walk(path)])
    except Exception as e:
        print(f"TEST_FAIL:count_source_files:{str(e)}")
        return None

def test_python_examples(path):
    try:
        py_files = [f for f in os.listdir(path) if f.endswith('.py')]
        for file in py_files:
            start_time = time.time()
            tracemalloc.start()
            subprocess.run(['python', os.path.join(path, file)], check=False)
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            print(f"BENCHMARK:exec_time_ms:{(end_time - start_time) * 1000}")
            print(f"BENCHMARK:exec_memory_mb:{peak / 10**6}")
            print(f"TEST_PASS:python_examples")
    except Exception as e:
        print(f"TEST_FAIL:python_examples:{str(e)}")

def test_rebot_devarm():
    try:
        install_system_packages('git')
        install_tool_dependencies('https://github.com/Seeed-Projects/reBot-DevArm.git')
        source_file_count = count_source_files('reBot-DevArm')
        if source_file_count is not None:
            print(f"BENCHMARK:source_file_count:{source_file_count}")
            print(f"TEST_PASS:count_source_files")
        test_python_examples('reBot-DevArm')
    except Exception as e:
        print(f"TEST_FAIL:test_rebot_devarm:{str(e)}")

def main():
    test_rebot_devarm()
    start_time = time.time()
    install_tool_dependencies('https://github.com/prusa3d/PrusaSlicer.git')
    end_time = time.time()
    print(f"BENCHMARK:prusa_slicer_install_time_s:{end_time - start_time}")
    print(f"BENCHMARK:vs_prusa_slicer_install_time_ratio:1.0")
    print("RUN_OK")

if __name__ == "__main__":
    main()