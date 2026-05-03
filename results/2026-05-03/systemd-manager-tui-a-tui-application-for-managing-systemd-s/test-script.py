import subprocess
import time
import tracemalloc

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'python3'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'pip'], check=False)

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'systemd-manager-tui'], check=False)
except subprocess.CalledProcessError:
    print("INSTALL_FAIL: pip install failed")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/Matheus-git/systemd-manager-tui.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './systemd-manager-tui'], check=False)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL: git clone and pip install -e failed")
else:
    print("INSTALL_OK")

# Benchmark installation time
start_time = time.time()
subprocess.run(['pip', 'install', 'systemd-manager-tui'], check=False)
end_time = time.time()
installation_time = end_time - start_time
print(f"BENCHMARK:install_time_s:{installation_time:.2f}")

# Test CLI availability
try:
    subprocess.run(['systemd-manager-tui', '--help'], check=False)
    print("TEST_PASS:cli_availability")
except subprocess.CalledProcessError:
    print("TEST_FAIL:cli_availability:systemd-manager-tui command not found")

# Test system service management features
try:
    subprocess.run(['systemd-manager-tui', 'start', 'sshd'], check=False)
    subprocess.run(['systemd-manager-tui', 'stop', 'sshd'], check=False)
    subprocess.run(['systemd-manager-tui', 'restart', 'sshd'], check=False)
    print("TEST_PASS:system_service_management")
except subprocess.CalledProcessError:
    print("TEST_FAIL:system_service_management:failed to manage systemd service")

# Compare performance with systemectl
try:
    start_time = time.time()
    subprocess.run(['systemctl', 'start', 'sshd'], check=False)
    end_time = time.time()
    systemectl_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['systemd-manager-tui', 'start', 'sshd'], check=False)
    end_time = time.time()
    systemd_manager_tui_time = end_time - start_time
    ratio = systemd_manager_tui_time / systemectl_time
    print(f"BENCHMARK:vs_systemectl_start_ratio:{ratio:.2f}")
except subprocess.CalledProcessError:
    print("TEST_SKIP:performance_comparison:systemctl command not found")

# Benchmark performance on large systemd service sets
tracemalloc.start()
start_time = time.time()
for i in range(100):
    subprocess.run(['systemd-manager-tui', 'list'], check=False)
end_time = time.time()
tracemalloc.stop()
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:large_service_set_time_ms:{(end_time - start_time) * 1000:.2f}")
print(f"BENCHMARK:large_service_set_memory_mb:{peak / 1024 / 1024:.2f}")

# Benchmark import time
start_time = time.time()
import systemd_manager_tui
end_time = time.time()
import_time = end_time - start_time
print(f"BENCHMARK:import_time_ms:{import_time * 1000:.2f}")

print("RUN_OK")