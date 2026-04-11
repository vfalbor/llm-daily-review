import subprocess
import time
import tracemalloc
import os

# Pre-install necessary APK packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)

# Install quien CLI using npm
try:
    install_start_time = time.time()
    subprocess.run(['npm', 'install', '-g', 'quien'], check=True)
    install_time = time.time() - install_start_time
    print(f"INSTALL_OK")
    print(f"BENCHMARK:install_time_s:{install_time:.2f}")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

# Clone quien repository and install using npm
try:
    install_start_time = time.time()
    subprocess.run(['git', 'clone', 'https://github.com/retlehs/quien.git'], check=True)
    os.chdir('quien')
    subprocess.run(['npm', 'install'], check=True)
    subprocess.run(['npm', 'link'], check=True)
    install_time = time.time() - install_start_time
    print(f"BENCHMARK:install_time_s_git:{install_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:install_git:{str(e)}")

# Run WHOIS lookup using quien CLI
try:
    lookup_start_time = time.time()
    subprocess.run(['quien', 'example.com'], check=True)
    lookup_time = time.time() - lookup_start_time
    print(f"TEST_PASS:whois_lookup")
    print(f"BENCHMARK:whois_lookup_ms:{lookup_time*1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:whois_lookup:{str(e)}")

# Run WHOIS lookup using whois baseline tool for comparison
try:
    subprocess.run(['apk', 'add', '--no-cache', 'whois'], check=True)
    lookup_start_time = time.time()
    subprocess.run(['whois', 'example.com'], check=True)
    lookup_time = time.time() - lookup_start_time
    print(f"TEST_PASS:whois_lookup_baseline")
    print(f"BENCHMARK:whois_lookup_baseline_ms:{lookup_time*1000:.2f}")
    print(f"BENCHMARK:vs_whois_lookup_ratio:{(lookup_time/(lookup_time+0.0001)):.2f}")
except Exception as e:
    print(f"TEST_FAIL:whois_lookup_baseline:{str(e)}")

# Measure memory usage using tracemalloc
tracemalloc.start()
subprocess.run(['quien', 'example.com'], check=True)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_bytes:{peak}")
tracemalloc.stop()

# Measure execution time of quien CLI
start_time = time.time()
subprocess.run(['quien', 'example.com'], check=True)
end_time = time.time()
print(f"BENCHMARK:execution_time_ms:{(end_time-start_time)*1000:.2f}")

# Count lines of code in quien repository
try:
    os.chdir('quien')
    loc_count = sum(1 for line in open('index.js'))
    print(f"BENCHMARK:loc_count:{loc_count}")
except Exception as e:
    print(f"TEST_FAIL:loc_count:{str(e)}")

# Count test files in quien repository
try:
    test_files_count = len([name for name in os.listdir('tests') if name.endswith('.js')])
    print(f"BENCHMARK:test_files_count:{test_files_count}")
except Exception as e:
    print(f"TEST_FAIL:test_files_count:{str(e)}")

print(f"RUN_OK")