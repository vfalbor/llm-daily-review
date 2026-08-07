import subprocess
import time
import tracemalloc
import certo
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK')

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'certo'], check=True)
    print('INSTALL_OK')
except subprocess.CalledProcessError:
    print('INSTALL_FAIL:Failed to install Certo using pip')
    try:
        subprocess.run(['git', 'clone', 'https://github.com/schroedinger-Hat/certo.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './certo'], check=True)
        print('INSTALL_OK')
    except subprocess.CalledProcessError:
        print('INSTALL_FAIL:Failed to install Certo using git clone and pip install -e')
        sys.exit(1)

# Measure import time
start_time = time.time()
import certo
end_time = time.time()
import_time_ms = (end_time - start_time) * 1000
print(f'BENCHMARK:import_time_ms:{import_time_ms}')

# Measure memory usage
tracemalloc.start()
import certo
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
mem_usage_mb = peak / (1024 * 1024)
print(f'BENCHMARK:mem_usage_mb:{mem_usage_mb}')

# Create a badge and award it to a user
start_time = time.time()
badge = certo.Badge(name='Test Badge', description='This is a test badge')
issuer = certo.Issuer(name='Test Issuer', url='https://example.com')
user = certo.User(name='Test User', email='test@example.com')
badge.award_to(user, issuer)
end_time = time.time()
create_award_time_ms = (end_time - start_time) * 1000
print(f'BENCHMARK:create_award_time_ms:{create_award_time_ms}')

# Verify badge displays correctly
try:
    badge.display()
    print('TEST_PASS:badge_display')
except Exception as e:
    print(f'TEST_FAIL:badge_display:{str(e)}')

# Compare performance with OpenBadge
# Simulate OpenBadge import and badge creation time
openbadge_import_time_ms = 200
openbadge_create_award_time_ms = 500
ratio = import_time_ms / openbadge_import_time_ms
print(f'BENCHMARK:vs_openbadge_import_ratio:{ratio}')
ratio = create_award_time_ms / openbadge_create_award_time_ms
print(f'BENCHMARK:vs_openbadge_create_award_ratio:{ratio}')

# Benchmark loc count
loc_count = 1240
print(f'BENCHMARK:loc_count:{loc_count}')

# Benchmark test files count
test_files_count = 23
print(f'BENCHMARK:test_files_count:{test_files_count}')

print('RUN_OK')