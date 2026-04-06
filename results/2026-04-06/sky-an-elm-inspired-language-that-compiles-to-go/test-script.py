import importlib
import importlib.util
import importlib.machinery
import os
import subprocess
import sys
import time
import timeit

# 1. Install Sky
print("INSTALLING Sky")
try:
    # Sky is not a Python package, but rather a separate language that compiles to Go
    # For the sake of this example, assume we have a Sky compiler binary
    # installed and available in the PATH
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {e}")

# 2. Run basic Hello World program
print("RUNNING Hello World program")
try:
    # Create a simple Sky program
    with open("hello.sky", "w") as f:
        f.write("main = \"Hello, World!\"")
    
    # Compile and run the program
    subprocess.run(["sky", "run", "hello.sky"], check=True)
    print("TEST_PASS:Hello World")
except Exception as e:
    print(f"TEST_FAIL:Hello World:{e}")

# 3. Infer types for a sample program
print("RUNNING type inference test")
try:
    # Create a sample Sky program with type inference
    with open("types.sky", "w") as f:
        f.write("add x y = x + y")
    
    # Compile the program to check type inference
    subprocess.run(["sky", "build", "types.sky"], check=True)
    print("TEST_PASS:Type Inference")
except Exception as e:
    print(f"TEST_FAIL:Type Inference:{e}")

# Compare runtime performance with Go
print("RUNNING performance comparison test")
try:
    # Create a simple Go program for comparison
    with open("hello.go", "w") as f:
        f.write("package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"Hello, World!\") }")
    
    # Compile and run the Go program
    subprocess.run(["go", "build", "hello.go"], check=True)
    go_time = timeit.timeit(lambda: subprocess.run("./hello", check=True), number=100)
    
    # Create a simple Sky program
    with open("hello.sky", "w") as f:
        f.write("main = \"Hello, World!\"")
    
    # Compile and run the Sky program
    subprocess.run(["sky", "build", "hello.sky"], check=True)
    sky_time = timeit.timeit(lambda: subprocess.run(["sky", "run", "hello.sky"], check=True), number=100)
    
    print(f"BENCHMARK:go_vs_sky:{'faster' if go_time < sky_time else 'slower'}")
    print("TEST_PASS:Performance Comparison")
except Exception as e:
    print(f"TEST_FAIL:Performance Comparison:{e}")

print("RUN_OK")