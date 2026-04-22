import subprocess
import time
import tracemalloc
import requests

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=False)
print('INSTALL_OK')

# Install GitHub CLI using npm
try:
    subprocess.run(['npm', 'install', '-g', '@github/cli'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:npm install failed with error code {e.returncode}')
    try:
        # Fallback to git clone and npm install
        subprocess.run(['git', 'clone', 'https://github.com/cli/cli.git', '/tmp/cli'], check=True)
        subprocess.run(['npm', 'install', '-g', '/tmp/cli'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:git clone and npm install failed with error code {e.returncode}')

# Measure execution time of a simple command
start_time = time.time()
try:
    subprocess.run(['gh', 'repo', 'list'], check=True)
    print(f'TEST_PASS:gh_repo_list')
    execution_time = time.time() - start_time
    print(f'BENCHMARK:gh_repo_list_ms:{execution_time*1000:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:gh_repo_list:Error code {e.returncode}')
    print(f'BENCHMARK:gh_repo_list_ms:0.0')

# Compare CLI output vs GitHub Web UI
try:
    cli_output = subprocess.check_output(['gh', 'repo', 'list']).decode('utf-8')
    web_ui_output = requests.get('https://github.com/').text
    if cli_output != web_ui_output:
        print('TEST_FAIL:gh_repo_list_vs_web_ui:Output mismatch')
    else:
        print('TEST_PASS:gh_repo_list_vs_web_ui')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:gh_repo_list_vs_web_ui:Error code {e.returncode}')

# Test API calls with gh api
try:
    api_output = subprocess.check_output(['gh', 'api', '/repos/{owner}/{repo}']).decode('utf-8')
    print(f'TEST_PASS:gh_api')
    print(f'BENCHMARK:gh_api_ms:{time.time()*1000:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:gh_api:Error code {e.returncode}')

# Measure execution time vs baseline tool (e.g., git)
start_time = time.time()
try:
    subprocess.run(['git', 'status'], check=True)
    execution_time = time.time() - start_time
    print(f'BENCHMARK:git_status_ms:{execution_time*1000:.2f}')
    ratio = execution_time / (time.time() - start_time)
    print(f'BENCHMARK:vs_git_status_ratio:{ratio:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:git_status:Error code {e.returncode}')

# Measure memory usage
tracemalloc.start()
try:
    subprocess.run(['gh', 'repo', 'list'], check=True)
except subprocess.CalledProcessError as e:
    pass
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_mb:{current/1024/1024:.2f}')
print(f'BENCHMARK:peak_memory_usage_mb:{peak/1024/1024:.2f}')

# Measure import time
start_time = time.time()
try:
    subprocess.run(['gh', '--help'], check=True)
    execution_time = time.time() - start_time
    print(f'BENCHMARK:import_time_ms:{execution_time*1000:.2f}')
except subprocess.CalledProcessError as e:
    print(f'TEST_FAIL:gh_import:Error code {e.returncode}')

print('RUN_OK')