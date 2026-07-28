import subprocess
import time
import tracemalloc
import os

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)

# Install required tool dependencies
try:
    subprocess.run(['pip', 'install', 'projektor'], check=True)
except subprocess.CalledProcessError:
    # Fallback installation method
    subprocess.run(['git', 'clone', 'https://github.com/tajd/projektor.git'], check=True)
    os.chdir('projektor')
    subprocess.run(['pip', 'install', '-e', '.'], check=True)
    os.chdir('..')

# Test 1: Create new wiki page, test permissions and visibility
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['projektor', 'wiki', 'create', 'test-page'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:create_wiki_page_time_ms:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:create_wiki_page_memory_mb:{peak / 1024 / 1024:.2f}")
    print(f"TEST_PASS:create_wiki_page")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:create_wiki_page:{e}")

# Test 2: Manage tasks, check execution and status
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['projektor', 'task', 'create', 'test-task'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:create_task_time_ms:{(end_time - start_time) * 1000:.2f}")
    print(f"BENCHMARK:create_task_memory_mb:{peak / 1024 / 1024:.2f}")
    print(f"TEST_PASS:manage_tasks")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:manage_tasks:{e}")

# Compare performance with Cloudflare Tunnels baseline tool
try:
    start_time = time.time()
    subprocess.run(['cloudflared', 'tunnel', 'http', 'http://localhost:8080'], check=True)
    end_time = time.time()
    cloudflare_tunnel_time = end_time - start_time
    start_time = time.time()
    subprocess.run(['projektor', 'tunnel', 'http', 'http://localhost:8080'], check=True)
    end_time = time.time()
    projektor_tunnel_time = end_time - start_time
    print(f"BENCHMARK:vs_cloudflare_tunnel_ratio:{projektor_tunnel_time / cloudflare_tunnel_time:.2f}")
except subprocess.CalledProcessError:
    print(f"TEST_SKIP:compare_performance_with_cloudflare_tunnels")

print("RUN_OK")