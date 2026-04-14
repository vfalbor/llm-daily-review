import subprocess
import time
import tracemalloc
import os

# Install necessary system packages
print("Installing system packages...")
subprocess.run(['apk', 'add', '--no-cache', 'go'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'cargo'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'nodejs'], check=False)
subprocess.run(['apk', 'add', '--no-cache', 'npm'], check=False)

# Install Lumina language
print("Installing Lumina language...")
try:
    subprocess.run(['go', 'get', 'github.com/nyigoro/lumina'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")
    exit(1)

# Clone Lumina repository
print("Cloning Lumina repository...")
try:
    subprocess.run(['git', 'clone', 'https://github.com/nyigoro/lumina-lang.git'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Build Lumina from source
print("Building Lumina from source...")
try:
    os.chdir('lumina-lang')
    subprocess.run(['cargo', 'build', '--release'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Test 1: Run 'hello world' via npm
print("Running Lumina 'hello world' via npm...")
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['npm', 'install'], check=True)
    subprocess.run(['lumina', 'run', 'examples/hello-world.lum'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:hello_world_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:hello_world_memory_mb:{peak / (1024 * 1024)}")
    print("TEST_PASS:hello_world")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:hello_world:{e}")
except Exception as e:
    print(f"TEST_FAIL:hello_world:{e}")

# Test 2: Run WASM example
print("Running Lumina WASM example...")
try:
    start_time = time.time()
    tracemalloc.start()
    subprocess.run(['lumina', 'compile', '--target', 'wasm32-unknown-unknown', 'examples/wasm-example.lum'], check=True)
    subprocess.run(['lumina', 'run', 'target/wasm32-unknown-unknown/release/wasm-example.wasm'], check=True)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:wasm_example_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:wasm_example_memory_mb:{peak / (1024 * 1024)}")
    print("TEST_PASS:wasm_example")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:wasm_example:{e}")
except Exception as e:
    print(f"TEST_FAIL:wasm_example:{e}")

# Test 3: Compile simple program and measure compile time
print("Compiling simple Lumina program...")
try:
    start_time = time.time()
    subprocess.run(['lumina', 'compile', 'examples/simple.lum'], check=True)
    end_time = time.time()
    compile_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:compile_time_ms:{compile_time_ms}")
    print("TEST_PASS:simple_program")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:simple_program:{e}")

# Compare performance vs baseline tool (Rust)
print("Comparing performance vs Rust...")
try:
    subprocess.run(['cargo', 'build', '--release', '--manifest-path', 'Cargo.toml'], check=True)
    rust_compile_time_ms = subprocess.check_output(['cargo', 'build', '--release', '--manifest-path', 'Cargo.toml']).decode('utf-8')
    rust_compile_time_ms = float(rust_compile_time_ms.split(' ')[-1].strip())
    ratio = compile_time_ms / rust_compile_time_ms
    print(f"BENCHMARK:vs_rust.compile_time_ms:{ratio}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:rust_comparison:{e}")

# Measure memory usage
print("Measuring memory usage...")
try:
    tracemalloc.start()
    subprocess.run(['lumina', 'compile', 'examples/simple.lum'], check=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_mb:{peak / (1024 * 1024)}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:memory_usage:{e}")

# Measure time to install Lumina
print("Measuring time to install Lumina...")
try:
    start_time = time.time()
    subprocess.run(['go', 'get', 'github.com/nyigoro/lumina'], check=True)
    end_time = time.time()
    install_time_ms = (end_time - start_time) * 1000
    print(f"BENCHMARK:install_time_ms:{install_time_ms}")
except subprocess.CalledProcessError as e:
    print(f"TEST_FAIL:install_time:{e}")

print("RUN_OK")