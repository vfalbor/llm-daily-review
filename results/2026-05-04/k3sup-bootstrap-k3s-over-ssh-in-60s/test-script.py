import subprocess
import time
import tracemalloc
import sys

def install_k3sup():
    try:
        start_time = time.time()
        subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm', 'git', 'cargo', 'rust'], check=True)
        subprocess.run(['npm', 'install', '-g', 'k3sup'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:install_time_s:{end_time - start_time}")
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")

def test_k3s_init():
    try:
        start_time = time.time()
        subprocess.run(['k3sup', 'init'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:k3s_init_time_s:{end_time - start_time}")
        print(f"TEST_PASS:k3s_init")
    except Exception as e:
        print(f"TEST_FAIL:k3s_init:{str(e)}")

def test_deploy_pod():
    try:
        start_time = time.time()
        subprocess.run(['k3s', 'kubectl', 'create', 'deployment', 'nginx', '--image=nginx'], check=True)
        subprocess.run(['k3s', 'kubectl', 'get', 'pods'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:deploy_pod_time_s:{end_time - start_time}")
        print(f"TEST_PASS:deploy_pod")
    except Exception as e:
        print(f"TEST_FAIL:deploy_pod:{str(e)}")

def test_k3s_cluster_creation():
    try:
        start_time = time.time()
        subprocess.run(['k3s', 'k3s', 'server'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:k3s_cluster_creation_time_s:{end_time - start_time}")
        print(f"TEST_PASS:k3s_cluster_creation")
    except Exception as e:
        print(f"TEST_FAIL:k3s_cluster_creation:{str(e)}")

def test_memory_usage():
    try:
        tracemalloc.start()
        subprocess.run(['k3s', 'k3s', 'server'], check=True)
        current, peak = tracemalloc.get_traced_memory()
        print(f"BENCHMARK:memory_usage_bytes:{peak}")
        tracemalloc.stop()
        print(f"TEST_PASS:memory_usage")
    except Exception as e:
        print(f"TEST_FAIL:memory_usage:{str(e)}")

def test_vs_kubernetes():
    try:
        start_time = time.time()
        subprocess.run(['kubectl', 'create', 'deployment', 'nginx', '--image=nginx'], check=True)
        end_time = time.time()
        kubernetes_time = end_time - start_time
        k3s_time = 0
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    mem_total = int(line.split()[1])
                    k3s_time = mem_total / 1024
        ratio = k3s_time / kubernetes_time
        print(f"BENCHMARK:vs_kubernetes_ratio:{ratio}")
        print(f"TEST_PASS:vs_kubernetes")
    except Exception as e:
        print(f"TEST_FAIL:vs_kubernetes:{str(e)}")

def main():
    install_k3sup()
    test_k3s_init()
    test_deploy_pod()
    test_k3s_cluster_creation()
    test_memory_usage()
    test_vs_kubernetes()
    print("RUN_OK")

if __name__ == '__main__':
    main()