import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

def install_davit():
    # Install required system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    
    # Try to install Davit using pip
    try:
        subprocess.run(['pip', 'install', 'davit'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install Davit using pip: {e}")
        
        # Fallback: clone from git and install
        subprocess.run(['git', 'clone', 'https://github.com/yourusername/davit.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './davit'], check=True, cwd='./davit')
        print("INSTALL_OK")

def run_davit():
    # Run a minimal functional test with synthetic data
    start_time = time.time()
    try:
        subprocess.run(['davit'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:run_davit_time_s:{end_time - start_time}")
        print(f"TEST_PASS:run_davit")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_davit:{e}")

def import_davit():
    # Measure import time
    start_time = time.time()
    try:
        spec = importlib.util.find_spec('davit')
        if spec is not None:
            importlib.machinery.ModuleSpec(spec).loader.exec_modulespec(spec)
            end_time = time.time()
            print(f"BENCHMARK:import_davit_time_ms:{(end_time - start_time) * 1000}")
            print(f"TEST_PASS:import_davit")
        else:
            print("TEST_FAIL:import_davit:Module not found")
    except Exception as e:
        print(f"TEST_FAIL:import_davit:{e}")

def compare_performance():
    # Compare performance with Docker
    start_time = time.time()
    subprocess.run(['docker', '--help'], check=True)
    end_time = time.time()
    docker_time = end_time - start_time
    
    start_time = time.time()
    subprocess.run(['davit'], check=True)
    end_time = time.time()
    davit_time = end_time - start_time
    
    ratio = davit_time / docker_time
    print(f"BENCHMARK:vs_docker_time_ratio:{ratio}")

def memory_benchmark():
    # Measure memory usage
    tracemalloc.start()
    subprocess.run(['davit'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_peak_mb:{peak / 10**6}")
    print(f"BENCHMARK:memory_usage_current_mb:{current / 10**6}")

def run_benchmarks():
    start_time = time.time()
    subprocess.run(['davit'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:davit_benchmark_time_s:{end_time - start_time}")
    
    start_time = time.time()
    subprocess.run(['docker', '--help'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:docker_benchmark_time_s:{end_time - start_time}")
    
    start_time = time.time()
    subprocess.run(['docker', 'run', '-it', 'alpine'], check=True)
    end_time = time.time()
    print(f"BENCHMARK:docker_run_benchmark_time_s:{end_time - start_time}")

def main():
    install_davit()
    import_davit()
    run_davit()
    compare_performance()
    memory_benchmark()
    run_benchmarks()
    print("RUN_OK")

if __name__ == "__main__":
    main()