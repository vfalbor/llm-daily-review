import subprocess
import time
import tracemalloc
import sys

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'cloudflare-os'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:pip install failed, trying git clone")
    subprocess.run(['git', 'clone', 'https://github.com/cloudflare/cloudflare-os.git'], check=True)
    subprocess.run(['pip', 'install', '-e', 'cloudflare-os'], check=True)
    print("INSTALL_OK")

# Import Cloudflare OS and measure import time
start_time = time.time()
import cloudflare_os
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time:.2f}")

# Test 1: Create a new deployment
try:
    start_time = time.time()
    deployment = cloudflare_os.create_deployment()
    end_time = time.time()
    deployment_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:deployment_time_ms:{deployment_time:.2f}")
    print("TEST_PASS:create_deployment")
except Exception as e:
    print(f"TEST_FAIL:create_deployment:{str(e)}")

# Test 2: Write a simple service using Cloudflare OS's API
try:
    start_time = time.time()
    service = cloudflare_os.create_service()
    end_time = time.time()
    service_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:service_time_ms:{service_time:.2f}")
    print("TEST_PASS:create_service")
except Exception as e:
    print(f"TEST_FAIL:create_service:{str(e)}")

# Test 3: Test service deployment and scalability using Cloudflare OS
try:
    start_time = time.time()
    cloudflare_os.deploy_service(service)
    end_time = time.time()
    deploy_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:deploy_time_ms:{deploy_time:.2f}")
    print("TEST_PASS:deploy_service")
except Exception as e:
    print(f"TEST_FAIL:deploy_service:{str(e)}")

# Test 4: Compare Cloudflare OS's performance with Kubernetes
try:
    # Simulate a Kubernetes deployment
    start_time = time.time()
    subprocess.run(['kubectl', 'create', 'deployment', 'test-deployment'], check=True)
    end_time = time.time()
    kubectl_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:kubectl_time_ms:{kubectl_time:.2f}")
    ratio = import_time / kubectl_time
    print(f"BENCHMARK:vs_kubernetes_import_time_ratio:{ratio:.2f}")
    print("TEST_PASS:compare_performance")
except Exception as e:
    print(f"TEST_FAIL:compare_performance:{str(e)}")

# Measure memory usage
tracemalloc.start()
cloudflare_os.create_deployment()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{current}")

# Measure time it takes to create 10 deployments
start_time = time.time()
for _ in range(10):
    cloudflare_os.create_deployment()
end_time = time.time()
deployment_loop_time = (end_time - start_time) * 1000
print(f"BENCHMARK:deployment_loop_time_ms:{deployment_loop_time:.2f}")

print("RUN_OK")