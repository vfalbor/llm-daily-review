import subprocess
import time
import tracemalloc
import importlib.util
import os

# Install necessary system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone GTFOBins repository
subprocess.run(['git', 'clone', 'https://github.com/GTFOBins/GTFOBins.github.io.git'], check=False)

# Install GTFOBins package
try:
    subprocess.run(['pip', 'install', 'gtfobins'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')
    try:
        subprocess.run(['pip', 'install', '-e', './GTFOBins.github.io/'], check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

# Import GTFOBins package and measure import time
start_time = time.time()
try:
    import gtfobins
    import_time = time.time() - start_time
    print(f'BENCHMARK:import_time_ms:{import_time * 1000:.2f}')
except Exception as e:
    print(f'TEST_FAIL:import_test:{str(e)}')

# Test privilege escalation
try:
    # Synthetic data for testing
    escalation_data = gtfobins.search('sudo')
    test_time = time.time()
    tracemalloc.start()
    gtfobins.exploit(escalation_data[0])
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    test_time = time.time() - test_time
    print(f'BENCHMARK:privilege_escalation_ms:{test_time * 1000:.2f}')
    print(f'BENCHMARK:privilege_escalation_memory_mb:{peak / (1024 * 1024):.2f}')
    print('TEST_PASS:privilege_escalation_test')
except Exception as e:
    print(f'TEST_FAIL:privilege_escalation_test:{str(e)}')

# Compare with LinuxExploitSuggester
try:
    import linux_exploit_suggester
    comparison_time = time.time()
    comparison_data = linux_exploit_suggester.search('sudo')
    comparison_time = time.time() - comparison_time
    comparison_ratio = test_time / comparison_time
    print(f'BENCHMARK:vs_linux_exploit_suggester_ratio:{comparison_ratio:.2f}')
    print(f'BENCHMARK:vs_linux_exploit_suggester_ms:{comparison_time * 1000:.2f}')
except Exception as e:
    print(f'TEST_SKIP:comparison_test:{str(e)}')

# Verify correct output for a specific vulnerability
try:
    vulnerability_data = gtfobins.search('CVE-2022-1234')
    test_time = time.time()
    tracemalloc.start()
    output = gtfobins.exploit(vulnerability_data[0])
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    test_time = time.time() - test_time
    print(f'BENCHMARK:vulnerability_output_time_ms:{test_time * 1000:.2f}')
    print(f'BENCHMARK:vulnerability_output_memory_mb:{peak / (1024 * 1024):.2f}')
    if 'exploit' in output:
        print('TEST_PASS:vulnerability_output_test')
    else:
        print('TEST_FAIL:vulnerability_output_test')
except Exception as e:
    print(f'TEST_FAIL:vulnerability_output_test:{str(e)}')

# Print final message
print('RUN_OK')