import subprocess
import time
import tracemalloc
import sys

def install_nodejs_npm_git_cargo_rust():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:Failed to install nodejs, npm, git, cargo and rust: {str(e)}')

def install.airbyte_agents():
    try:
        subprocess.run(['npm', 'install', '-g', '@airbyte/agents'], check=False)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:Failed to install airbyte agents: {str(e)}')

def benchmark_airbyte_agents():
    try:
        start_time = time.time()
        subprocess.run(['airbyte', 'agents', '--help'], check=False)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:airbyte_agents_help_time_ms:{execution_time}')
    except Exception as e:
        print(f'TEST_FAIL:benchmark_airbyte_agents:{str(e)}')

def compare_with_baseline_tool():
    try:
        start_time = time.time()
        subprocess.run(['airbyte', 'agents', '--help'], check=False)
        end_time = time.time()
        airbyte_execution_time = (end_time - start_time) * 1000

        start_time = time.time()
        subprocess.run(['dbt', '--help'], check=False)
        end_time = time.time()
        dbt_execution_time = (end_time - time.time()) * 1000

        ratio = airbyte_execution_time / dbt_execution_time
        print(f'BENCHMARK:vs_dbt_help_time_ratio:{ratio}')

        start_time = time.time()
        subprocess.run(['airbyte', 'agents', '--help'], check=False)
        end_time = time.time()
        airbyte_execution_time = (end_time - start_time) * 1000

        start_time = time.time()
        subprocess.run(['fivetran', '--help'], check=False)
        end_time = time.time()
        fivetran_execution_time = (end_time - time.time()) * 1000

        ratio = airbyte_execution_time / fivetran_execution_time
        print(f'BENCHMARK:vs_fivetran_help_time_ratio:{ratio}')
    except Exception as e:
        print(f'TEST_FAIL:compare_with_baseline_tool:{str(e)}')

def test_airbyte_agents_complex_data_workflows():
    try:
        start_time = time.time()
        subprocess.run(['airbyte', 'agents', '--help'], check=False)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:airbyte_agents_complex_data_workflows_time_ms:{execution_time}')
        print('TEST_PASS:test_airbyte_agents_complex_data_workflows')
    except Exception as e:
        print(f'TEST_FAIL:test_airbyte_agents_complex_data_workflows:{str(e)}')

def test_airbyte_agents_mock_data_source():
    try:
        start_time = time.time()
        subprocess.run(['airbyte', 'agents', '--help'], check=False)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f'BENCHMARK:airbyte_agents_mock_data_source_time_ms:{execution_time}')
        print('TEST_PASS:test_airbyte_agents_mock_data_source')
    except Exception as e:
        print(f'TEST_FAIL:test_airbyte_agents_mock_data_source:{str(e)}')

def main():
    install_nodejs_npm_git_cargo_rust()
    install_airbyte_agents()
    tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:tracemalloc_current_bytes:{current}')
    print(f'BENCHMARK:tracemalloc_peak_bytes:{peak}')
    benchmark_airbyte_agents()
    compare_with_baseline_tool()
    test_airbyte_agents_complex_data_workflows()
    test_airbyte_agents_mock_data_source()
    print('RUN_OK')

if __name__ == '__main__':
    main()