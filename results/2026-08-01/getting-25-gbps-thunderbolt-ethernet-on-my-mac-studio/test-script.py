import subprocess
import time
import tracemalloc
import os

# Install required system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install required system packages: {e}")
    exit(1)

print("INSTALL_OK")

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'speedtest-cli'], check=True)
except subprocess.CalledProcessError as e:
    try:
        subprocess.run(['git', 'clone', 'https://github.com/sivel/speedtest-cli.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './speedtest-cli'], check=True, cwd='./speedtest-cli')
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install tool dependencies: {e}")
        exit(1)

print("INSTALL_OK")

# Basic run test
try:
    import speedtest
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    download = s.download()
    upload = s.upload()
    print(f"BENCHMARK:speedtest_download_mbps:{download / 10**6:.2f}")
    print(f"BENCHMARK:speedtest_upload_mbps:{upload / 10**6:.2f}")
    print("TEST_PASS:speedtest_basic")
except Exception as e:
    print(f"TEST_FAIL:speedtest_basic:{e}")

# Measure performance test
try:
    tracemalloc.start()
    start_time = time.time()
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    download = s.download()
    upload = s.upload()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:speedtest_import_time_ms:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:speedtest_memory_usage_mb:{peak / 10**6:.2f}")
    print("TEST_PASS:speedtest_performance")
except Exception as e:
    print(f"TEST_FAIL:speedtest_performance:{e}")

# Compare vs similar tool test
try:
    import psutil
    s = speedtest.Speedtest()
    s.get_servers()
    s.get_best_server()
    download = s.download()
    upload = s.upload()
    psutil_download = sum([nic.statistics()['bytes_sent'] for nic in psutil.net_if_addrs().values()])
    psutil_upload = sum([nic.statistics()['bytes_recv'] for nic in psutil.net_if_addrs().values()])
    print(f"BENCHMARK:vs_psutil_speedtest_download_ratio:{download / psutil_download:.2f}")
    print(f"BENCHMARK:vs_psutil_speedtest_upload_ratio:{upload / psutil_upload:.2f}")
    print("TEST_PASS:speedtest_comparison")
except Exception as e:
    print(f"TEST_FAIL:speedtest_comparison:{e}")

print("RUN_OK")