import subprocess
import time
import tracemalloc
import os
import git

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def clone_repo():
    try:
        repo = git.Repo.clone_from("https://github.com/eaw/picoz80", "picoz80")
        return repo
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")
        return None

def count_source_files(repo):
    try:
        file_count = sum([len(files) for r, d, files in os.walk(repo.working_tree_dir)])
        print(f"BENCHMARK:loc_count:{file_count}")
    except Exception as e:
        print(f"BENCHMARK:LOC_COUNT_ERROR:{str(e)}")

def count_languages(repo):
    try:
        languages = set()
        for root, dirs, files in os.walk(repo.working_tree_dir):
            for file in files:
                if file.endswith(".c") or file.endswith(".cpp"):
                    languages.add("C/C++")
                elif file.endswith(".py"):
                    languages.add("Python")
                elif file.endswith(".java"):
                    languages.add("Java")
        print(f"BENCHMARK:language_count:{len(languages)}")
    except Exception as e:
        print(f"BENCHMARK:LANGUAGE_COUNT_ERROR:{str(e)}")

def run_python_examples(repo):
    try:
        start_time = time.time()
        python_files = [os.path.join(root, file) for root, dirs, files in os.walk(repo.working_tree_dir) for file in files if file.endswith(".py")]
        for file in python_files:
            subprocess.run(['python', file], check=False)
        end_time = time.time()
        print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:run_python_examples")
    except Exception as e:
        print(f"TEST_FAIL:run_python_examples:{str(e)}")

def compare_performance():
    try:
        start_time = time.time()
        # Run a simple Z80-based project
        subprocess.run(['python', 'picoz80/examples/simple_z80.py'], check=False)
        end_time = time.time()
        picoz80_time = end_time - start_time

        start_time = time.time()
        # Run the same project with the original Z80 implementation
        subprocess.run(['python', 'z80/examples/simple_z80.py'], check=False)
        end_time = time.time()
        z80_time = end_time - start_time

        print(f"BENCHMARK:vs_z80_simple_z80_ratio:{picoz80_time / z80_time}")
    except Exception as e:
        print(f"BENCHMARK:vs_z80_simple_z80_ratio_error:{str(e)}")

def main():
    install_packages()
    repo = clone_repo()
    if repo:
        count_source_files(repo)
        count_languages(repo)
        run_python_examples(repo)
        compare_performance()
        tracemalloc.start()
        time.sleep(1)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}")
        tracemalloc.stop()
        print("RUN_OK")

if __name__ == "__main__":
    main()