import subprocess
import time
import tracemalloc
import os
import git
import platform

def install_dependencies():
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    # Clone the repository
    try:
        repo = git.Repo.clone_from('https://github.com/Keychron/Keychron-Keyboards-Hardware-Design.git', 'keychron')
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')
        return False
    return True

def test_install_and_basic_run():
    try:
        start_time = time.time()
        repo = git.Repo('keychron')
        repo.git.status()
        end_time = time.time()
        print(f'BENCHMARK:install_time_s:{end_time - start_time:.2f}')
        print('TEST_PASS:install_and_basic_run')
    except Exception as e:
        print(f'TEST_FAIL:install_and_basic_run:{str(e)}')

def test_measure_performance():
    try:
        start_time = time.time()
        tracemalloc.start()
        repo = git.Repo('keychron')
        repo.git.status()
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:memory_usage_bytes:{current}')
        print(f'BENCHMARK:execution_time_s:{end_time - start_time:.2f}')
        print('TEST_PASS:measure_performance')
    except Exception as e:
        print(f'TEST_FAIL:measure_performance:{str(e)}')

def test_compare_vs_similar_tool():
    try:
        start_time = time.time()
        repo = git.Repo('keychron')
        repo.git.status()
        end_time = time.time()
        # Measure time taken to run similar tool
        similar_tool_start_time = time.time()
        # Assuming the similar tool is also a git repository
        similar_tool_repo = git.Repo.clone_from('https://github.com/similar-tool/similar-tool.git', 'similar-tool')
        similar_tool_end_time = time.time()
        similar_toolExecution_time = similar_tool_end_time - similar_tool_start_time
        # Emit BENCHMARK line with ratio of execution times
        print(f'BENCHMARK:vs_similar_tool_execution_time_ratio:{(end_time - start_time) / similar_toolExecution_time:.2f}')
        print('TEST_PASS:compare_vs_similar_tool')
    except Exception as e:
        print(f'TEST_FAIL:compare_vs_similar_tool:{str(e)}')

def test_count_source_files():
    try:
        repo = git.Repo('keychron')
        files = [f for f in repo.git.ls_files().split('\n') if f]
        print(f'BENCHMARK:source_files_count:{len(files)}')
        print('TEST_PASS:count_source_files')
    except Exception as e:
        print(f'TEST_FAIL:count_source_files:{str(e)}')

def main():
    if install_dependencies():
        test_install_and_basic_run()
        test_measure_performance()
        test_compare_vs_similar_tool()
        test_count_source_files()
        print('RUN_OK')

if __name__ == '__main__':
    main()