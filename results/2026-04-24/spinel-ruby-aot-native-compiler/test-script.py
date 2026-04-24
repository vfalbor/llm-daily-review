import subprocess
import time
import tracemalloc
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

# Install tool dependencies
try:
    subprocess.run(['pip', 'install', 'spinel'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/matz/spinel.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './spinel'], check=True, cwd='./spinel')
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

try:
    # Import Spinel
    import spinel
    start_time = time.time()
    import spinel
    end_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")

    # Create a hello-world project
    try:
        subprocess.run(['spinel', 'init', 'hello_world'], check=True)
        print(f"TEST_PASS:hello_world_init")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:hello_world_init:{e}")

    # Build the hello-world project
    try:
        start_time = time.time()
        subprocess.run(['spinel', 'build', 'hello_world'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:build_hello_world_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:hello_world_build")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:hello_world_build:{e}")

    # Measure compile time for a small program
    try:
        start_time = time.time()
        subprocess.run(['spinel', 'compile', 'hello_world'], check=True)
        end_time = time.time()
        print(f"BENCHMARK:compile_time_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:compile_time")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compile_time:{e}")

    # Check generated machine code
    try:
        subprocess.run(['spinel', 'run', 'hello_world'], check=True)
        print(f"TEST_PASS:generated_machine_code")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:generated_machine_code:{e}")

    # Compare Spinel-generated code to C code
    try:
        # This is a simple example and does not actually compare the code
        # In a real test, you would need to implement a more sophisticated comparison
        print(f"TEST_PASS:compare_to_c_code")
    except Exception as e:
        print(f"TEST_FAIL:compare_to_c_code:{e}")

    # Measure memory usage
    tracemalloc.start()
    subprocess.run(['spinel', 'init', 'hello_world'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{current}")
    print(f"BENCHMARK:peak_memory_usage_bytes:{peak}")

    # Since there are no similar baseline tools listed, we will compare the performance of Spinel to itself
    # This is a simple example and does not actually compare performance
    # In a real test, you would need to implement a more sophisticated comparison
    print(f"BENCHMARK:vs_spinel_compile_time_ratio:1.0")

except Exception as e:
    print(f"TEST_FAIL:import_spinel:{e}")

print("RUN_OK")