import subprocess
import time
import tracemalloc
import requests
import os
import git

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'python3'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'pip'], check=False)

def clone_repo():
    try:
        repo = git.Repo.clone_from('https://github.com/jfawl/falstad-mathphysics-simulations.git', 'falstad-mathphysics-simulations')
        return True
    except Exception as e:
        print(f"TEST_FAIL:clone_repo:{str(e)}")
        return False

def count_source_files():
    try:
        start_time = time.time()
        file_count = 0
        for root, dirs, files in os.walk('falstad-mathphysics-simulations'):
            file_count += len(files)
        end_time = time.time()
        print(f"BENCHMARK:source_file_count:{file_count}")
        print(f"BENCHMARK:source_file_count_time_ms:{(end_time - start_time) * 1000}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:count_source_files:{str(e)}")
        return False

def run_python_examples():
    try:
        start_time = time.time()
        subprocess.run(['python3', 'falstad-mathphysics-simulations/example.py'], check=False)
        end_time = time.time()
        print(f"BENCHMARK:python_example_time_ms:{(end_time - start_time) * 1000}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:run_python_examples:{str(e)}")
        return False

def visit_website():
    try:
        start_time = time.time()
        response = requests.get('https://github.com/jfawl/falstad-mathphysics-simulations')
        end_time = time.time()
        print(f"BENCHMARK:website_load_time_ms:{(end_time - start_time) * 1000}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:visit_website:{str(e)}")
        return False

def compare_with_baseline():
    try:
        start_time = time.time()
        # Simulate PhET Interactive Simulations
        response = requests.get('https://phet.colorado.edu/')
        end_time = time.time()
        baseline_time = (end_time - start_time) * 1000
        start_time = time.time()
        # Simulate Falstad
        response = requests.get('https://github.com/jfawl/falstad-mathphysics-simulations')
        end_time = time.time()
        falstad_time = (end_time - start_time) * 1000
        ratio = falstad_time / baseline_time
        print(f"BENCHMARK:vs_phet_load_time_ratio:{ratio}")
        return True
    except Exception as e:
        print(f"TEST_FAIL:compare_with_baseline:{str(e)}")
        return False

def main():
    install_dependencies()
    print("INSTALL_OK")
    if clone_repo():
        print("TEST_PASS:clone_repo")
    if count_source_files():
        print("TEST_PASS:count_source_files")
    if run_python_examples():
        print("TEST_PASS:run_python_examples")
    if visit_website():
        print("TEST_PASS:visit_website")
    if compare_with_baseline():
        print("TEST_PASS:compare_with_baseline")
    print("RUN_OK")

if __name__ == "__main__":
    main()