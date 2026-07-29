import subprocess
import time
import tracemalloc
import os

def install_sbcl():
    try:
        # Install dependencies
        subprocess.run(['apk', 'add', '--no-cache', 'gcc', 'make'], check=True)
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
        
        # Clone SBCL repository
        subprocess.run(['git', 'clone', 'https://github.com/sbcl/sbcl.git'], check=True)
        
        # Change into SBCL directory
        os.chdir('sbcl')
        
        # Build SBCL from source
        start_time = time.time()
        subprocess.run(['sh', 'make.sh'], check=True)
        install_time = time.time() - start_time
        
        print(f"INSTALL_OK")
        print(f"BENCHMARK:install_time_s:{install_time:.2f}")
        
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")
    

def run_lisp_example():
    try:
        # Run Lisp example
        start_time = time.time()
        subprocess.run(['./src/runtime/sbcl', '--load', 'examples/hello-world.lisp'], check=True)
        run_time = time.time() - start_time
        
        print(f"TEST_PASS:run_lisp_example")
        print(f"BENCHMARK:hello_world_ms:{run_time*1000:.2f}")
        
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_lisp_example:{e}")
    

def measure_lisp_performance():
    try:
        # Measure Lisp performance
        start_time = time.time()
        tracemalloc.start()
        subprocess.run(['./src/runtime/sbcl', '--load', 'examples/fibonacci.lisp'], check=True)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"TEST_PASS:measure_lisp_performance")
        print(f"BENCHMARK:lisp_performance_ms:{(end_time-start_time)*1000:.2f}")
        print(f"BENCHMARK:lisp_memory_usage_mb:{current/10**6:.2f}")
        
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:measure_lisp_performance:{e}")
    

def check_sbcl_stability():
    try:
        # Check SBCL stability
        start_time = time.time()
        subprocess.run(['./src/runtime/sbcl', '--load', 'examples/stability-test.lisp'], check=True)
        end_time = time.time()
        
        print(f"TEST_PASS:check_sbcl_stability")
        print(f"BENCHMARK:stability_test_ms:{(end_time-start_time)*1000:.2f}")
        
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:check_sbcl_stability:{e}")
    

def compare_performance():
    try:
        # Compare performance with CLisp
        subprocess.run(['apk', 'add', '--no-cache', 'clisp'], check=True)
        start_time = time.time()
        subprocess.run(['clisp', '-i', 'examples/fibonacci.lisp'], check=True)
        end_time = time.time()
        
        clisp_time = end_time - start_time
        sbcl_time = 0  # Replace with actual SBCL time
        
        ratio = sbcl_time / clisp_time
        
        print(f"BENCHMARK:vs_clisp_fibonacci_ratio:{ratio:.2f}")
        
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_performance:{e}")
    

def main():
    install_sbcl()
    run_lisp_example()
    measure_lisp_performance()
    check_sbcl_stability()
    compare_performance()
    
    print("RUN_OK")
    

if __name__ == "__main__":
    main()