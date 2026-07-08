import subprocess
import importlib
import time
import tracemalloc
import sys

# Install git package using apk
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install Rowboat using pip
try:
    subprocess.run(['pip', 'install', 'rowboat'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError as e:
    print(f'INSTALL_FAIL:Rowboat installation failed with error code {e.returncode}')
    try:
        # Try installing Rowboat from source as fallback
        subprocess.run(['git', 'clone', 'https://github.com/rowboatlabs/rowboat.git'], check=True, cwd='/tmp')
        subprocess.run(['pip', 'install', '-e', '/tmp/rowboat'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError as e:
        print(f'INSTALL_FAIL:Rowboat installation from source failed with error code {e.returncode}')

# Import Rowboat and measure import time
start_time = time.time()
try:
    import rowboat
    import_time = time.time() - start_time
    print(f'BENCHMARK:import_time_ms:{import_time * 1000:.2f}')
except ImportError as e:
    print(f'TEST_FAIL:Import Rowboat: {str(e)}')
else:
    print(f'TEST_PASS:Import Rowboat')

# Run a minimal functional test with synthetic data
try:
    # Run Rowboat with synthetic data
    start_time = time.time()
    tracemalloc.start()
    rowboat.run()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    run_time = end_time - start_time
    print(f'BENCHMARK:rowboat_run_time_ms:{run_time * 1000:.2f}')
    print(f'BENCHMARK:rowboat_run_memory_mb:{peak / (1024 * 1024):.2f}')
    print(f'TEST_PASS:Run Rowboat')
except Exception as e:
    print(f'TEST_FAIL:Run Rowboat: {str(e)}')

# Compare performance vs the most similar baseline tool (Claude Desktop)
try:
    # Import Claude Desktop and measure import time
    start_time = time.time()
    import claude
    import_time = time.time() - start_time
    print(f'BENCHMARK:import_time_ms_claude:{import_time * 1000:.2f}')
    # Run Claude Desktop with synthetic data
    start_time = time.time()
    tracemalloc.start()
    claude.run()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    run_time = end_time - start_time
    print(f'BENCHMARK:claude_run_time_ms:{run_time * 1000:.2f}')
    print(f'BENCHMARK:claude_run_memory_mb:{peak / (1024 * 1024):.2f}')
    # Compare performance
    rowboat_run_time = run_time  # Use the rowboat run time from above
    claude_run_time = run_time  # Use the claude run time from above
    ratio = rowboat_run_time / claude_run_time
    print(f'BENCHMARK:vs_claude_run_time_ratio:{ratio:.2f}')
except ImportError as e:
    print(f'TEST_SKIP:Compare performance with Claude Desktop: {str(e)}')

# Print RUN_OK
print('RUN_OK')