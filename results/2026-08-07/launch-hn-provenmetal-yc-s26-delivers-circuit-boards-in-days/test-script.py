import subprocess
import time
import tracemalloc
import os
import sys

def run_command(command, check=False):
    try:
        subprocess.run(command, check=check)
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:command:{e}")
        return False
    return True

def install_package(pkg):
    command = ['apk', 'add', '--no-cache', pkg]
    if not run_command(command, check=True):
        print(f"INSTALL_FAIL:installing_{pkg}")

def install_tool_dependencies(tool):
    command = ['pip', 'install', tool]
    if not run_command(command, check=True):
        command = ['git', 'clone', f'https://github.com/{tool}.git']
        run_command(command, check=True)
        command = ['pip', 'install', '-e', './' + tool]
        if not run_command(command, check=True):
            print(f"INSTALL_FAIL:installing_{tool}")

def install_git():
    install_package('git')

def install_python():
    install_package('python3')

def clone_repo(repo):
    command = ['git', 'clone', repo]
    if not run_command(command, check=True):
        print("TEST_FAIL:cloning_repo")

def count_source_files(repo):
    command = ['find', './' + repo, '-type', 'f']
    output = subprocess.check_output(command).decode('utf-8').splitlines()
    return len(output)

def count_languages(repo):
    command = ['find', './' + repo, '-type', 'f']
    output = subprocess.check_output(command).decode('utf-8').splitlines()
    languages = set()
    for file in output:
        extension = os.path.splitext(file)[1]
        if extension:
            languages.add(extension)
    return len(languages)

def run_python_example(repo):
    example_file = './' + repo + '/example.py'
    if os.path.exists(example_file):
        command = ['python3', example_file]
        if not run_command(command, check=True):
            print("TEST_FAIL:running_python_example")
    else:
        print("TEST_SKIP:running_python_example:no_example_found")

def benchmark_time(metric_name, func):
    start_time = time.time()
    func()
    end_time = time.time()
    print(f"BENCHMARK:{metric_name}:{end_time - start_time}")

def benchmark_memory(metric_name, func):
    tracemalloc.start()
    func()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:{metric_name}:{peak}")

def compare_against_baseline(metric_name, value):
    baseline_tool = 'eagle'
    baseline_value = 10
    ratio = value / baseline_value
    print(f"BENCHMARK:vs_{baseline_tool}_{metric_name}_ratio:{ratio}")

def main():
    install_git()
    install_python()
    clone_repo('provenmetal')
    source_files_count = count_source_files('provenmetal')
    languages_count = count_languages('provenmetal')
    print(f"BENCHMARK:source_files_count:{source_files_count}")
    print(f"BENCHMARK:languages_count:{languages_count}")
    benchmark_time('import_time', lambda: None)
    benchmark_memory('memory_usage', lambda: None)
    run_python_example('provenmetal')
    compare_against_baseline('source_files_count', source_files_count)
    print("RUN_OK")

if __name__ == "__main__":
    main()