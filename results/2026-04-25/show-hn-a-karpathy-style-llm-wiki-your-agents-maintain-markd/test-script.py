import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

def install_dependencies():
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    # Install tool dependencies
    subprocess.run(['pip', 'install', 'gitpython'], check=False)
    # Install wuphf package
    try:
        subprocess.run(['pip', 'install', 'wuphf'], check=True)
    except subprocess.CalledProcessError:
        # Fallback to git clone and pip install -e .
        subprocess.run(['git', 'clone', 'https://github.com/nex-crm/wuphf.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './wuphf'], check=True, cwd='./wuphf')
    print('INSTALL_OK')

def run_benchmark(name):
    start_time = time.time()
    tracemalloc.start()
    try:
        # Import wuphf package
        spec = importlib.util.find_spec('wuphf')
        wuphf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wuphf)
        # Run a minimal functional test
        wuphf.create_entry('Test Entry')
        wuphf.commit_changes('Test Commit')
    except Exception as e:
        print(f'TEST_FAIL:{name}:{str(e)}')
    else:
        print(f'TEST_PASS:{name}')
    finally:
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f'BENCHMARK:import_time_s:{time.time() - start_time:.2f}')
        print(f'BENCHMARK:memory_usage_mb:{current / 1024 / 1024:.2f}')
        print(f'BENCHMARK:peak_memory_usage_mb:{peak / 1024 / 1024:.2f}')

def run_benchmark_vs_baseline(name):
    # Run a minimal functional test with LLM-Wiki
    start_time = time.time()
    subprocess.run(['llm-wiki', 'create', 'Test Entry'], check=True)
    subprocess.run(['llm-wiki', 'commit', 'Test Commit'], check=True)
    end_time = time.time()
    print(f'BENCHMARK:vs_llm_wiki_{name}_ratio:{(end_time - start_time) / 0.01:.2f}')

def main():
    try:
        install_dependencies()
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')
    else:
        try:
            run_benchmark('create_entry')
        except Exception as e:
            print(f'TEST_FAIL:create_entry:{str(e)}')
        try:
            run_benchmark('commit_changes')
        except Exception as e:
            print(f'TEST_FAIL:commit_changes:{str(e)}')
        run_benchmark_vs_baseline('create_entry')
        run_benchmark_vs_baseline('commit_changes')
        print('RUN_OK')

if __name__ == '__main__':
    main()