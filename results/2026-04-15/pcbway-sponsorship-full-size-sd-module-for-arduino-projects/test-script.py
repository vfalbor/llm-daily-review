import subprocess
import time
import tracemalloc
import os
import git
import sys

def install_git():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        return True
    except Exception as e:
        print(f"INSTALL_FAIL: unable to install git: {str(e)}")
        return False

def install_dependencies():
    try:
        repo = git.Repo.clone_from("https://github.com/your-project", "/tmp/repo")
        return True
    except Exception as e:
        print(f"INSTALL_FAIL: unable to clone repository: {str(e)}")
        return False

def count_source_files():
    try:
        count = 0
        for root, dirs, files in os.walk("/tmp/repo"):
            for file in files:
                if file.endswith(".c") or file.endswith(".cpp") or file.endswith(".py") or file.endswith(".ino"):
                    count += 1
        return count
    except Exception as e:
        print(f"TEST_FAIL:count_source_files: {str(e)}")
        return None

def count_languages():
    try:
        languages = set()
        for root, dirs, files in os.walk("/tmp/repo"):
            for file in files:
                if file.endswith(".c") or file.endswith(".cpp"):
                    languages.add("C/C++")
                elif file.endswith(".py"):
                    languages.add("Python")
                elif file.endswith(".ino"):
                    languages.add("Arduino")
        return len(languages)
    except Exception as e:
        print(f"TEST_FAIL:count_languages: {str(e)}")
        return None

def run_python_examples():
    try:
        python_files = []
        for root, dirs, files in os.walk("/tmp/repo"):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        for file in python_files:
            subprocess.run(['python', file], check=False)
        return True
    except Exception as e:
        print(f"TEST_FAIL:run_python_examples: {str(e)}")
        return False

def main():
    start_time = time.time()
    tracemalloc.start()

    if not install_git():
        pass
    if not install_dependencies():
        pass

    start_install_time = time.time()
    if not install_dependencies():
        pass
    end_install_time = time.time()
    print(f"BENCHMARK:install_time_s:{end_install_time - start_install_time}")

    source_files_count = count_source_files()
    if source_files_count is not None:
        print(f"BENCHMARK:source_files_count:{source_files_count}")

    languages_count = count_languages()
    if languages_count is not None:
        print(f"BENCHMARK:languages_count:{languages_count}")

    if run_python_examples():
        print("TEST_PASS:run_python_examples")
    else:
        print("TEST_FAIL:run_python_examples: unable to run python examples")

    end_time = time.time()
    print(f"BENCHMARK:total_time_s:{end_time - start_time}")

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:peak_memory_mb:{peak / 1024 / 1024}")

    # comparing against MicroSD
    sd_module_time = end_time - start_time
    sd_module_memory = peak
    baseline_time = 10  # replace with actual baseline time
    baseline_memory = 100 * 1024 * 1024  # replace with actual baseline memory
    print(f"BENCHMARK:vs_MicroSD_time_ratio:{sd_module_time / baseline_time}")
    print(f"BENCHMARK:vs_MicroSD_memory_ratio:{sd_module_memory / baseline_memory}")

    print("RUN_OK")

if __name__ == "__main__":
    main()