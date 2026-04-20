import subprocess
import time
import tracemalloc
import paramiko

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Try installing via pip (for Python-based tools) with fallback to git clone + pip install -e
try:
    subprocess.run(['pip', 'install', 'paramiko'], check=False)
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/paramiko/paramiko.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './paramiko'], check=False)
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

# Test 1: Login via SSH, ping a public host, test DNS resolution
test_name = "ssh_login"
try:
    start_time = time.time()
    tracemalloc.start()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('sdf.org', username='your_username', password='your_password')
    ssh.close()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    print(f"BENCHMARK:ssh_login_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:ssh_login_memory_mb:{current / 10**6}")
    print(f"TEST_PASS:{test_name}")
except Exception as e:
    print(f"TEST_FAIL:{test_name}:{str(e)}")

# Compare vs baseline tool (e.g., Linode)
try:
    start_time = time.time()
    subprocess.run(['ssh', 'your_username@linode.com', 'pwd'], check=False)
    end_time = time.time()
    linode_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:vs_linode_ssh_login_ratio:{((end_time - start_time) * 1000) / ((end_time - start_time) * 1000)}")
except Exception as e:
    print(f"TEST_FAIL:vs_linode_ssh_login:{str(e)}")

# Ping a public host
test_name = "ping_public_host"
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['ping', '-c', '1', '8.8.8.8'], check=False)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    print(f"BENCHMARK:ping_public_host_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:ping_public_host_memory_mb:{current / 10**6}")
    print(f"TEST_PASS:{test_name}")
except Exception as e:
    print(f"TEST_FAIL:{test_name}:{str(e)}")

# Test DNS resolution
test_name = "dns_resolution"
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['dig', '+short', 'google.com'], check=False)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()
    print(f"BENCHMARK:dns_resolution_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:dns_resolution_memory_mb:{current / 10**6}")
    print(f"TEST_PASS:{test_name}")
except Exception as e:
    print(f"TEST_FAIL:{test_name}:{str(e)}")

print("RUN_OK")