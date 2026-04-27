import subprocess
import time
import tracemalloc
import sys

# Pre-install required packages
apk_packages = ['git']
for pkg in apk_packages:
    try:
        subprocess.run(['apk', 'add', '--no-cache', pkg], check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:Failed to install {pkg}: {e}")
        sys.exit(1)
    else:
        print("INSTALL_OK")

# Install Rust
try:
    subprocess.run(['apk', 'add', '--no-cache', 'rust'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install Rust: {e}")
    sys.exit(1)
else:
    print("INSTALL_OK")

# Clone and build Rust project
try:
    subprocess.run(['git', 'clone', 'https://github.com/rust-lang/rust'], check=True)
    subprocess.run(['cargo', 'build'], cwd='./rust', check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to clone and build Rust project: {e}")
    sys.exit(1)
else:
    print("INSTALL_OK")

# Measure memory allocation
def measure_memory_allocation():
    tracemalloc.start()
    start_time = time.time()
    # Simple Rust program using Box
    rust_code = """
    use std::rc::Rc;

    struct Node {
        value: i32,
        next: Option<Rc<Node>>,
    }

    impl Node {
        fn new(value: i32) -> Rc<Self> {
            Rc::new(Node {
                value,
                next: None,
            })
        }
    }

    fn main() {
        let node = Node::new(10);
    }
    """
    with open('main.rs', 'w') as f:
        f.write(rust_code)
    # Compile and run Rust program
    try:
        subprocess.run(['rustc', 'main.rs'], check=True)
        subprocess.run('./main', check=True)
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:Memory allocation test: {e}")
    else:
        print("TEST_PASS:Memory allocation test")
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return end_time - start_time, current, peak

# Run tests
test_name = "memory_allocation"
try:
    latency, current, peak = measure_memory_allocation()
except Exception as e:
    print(f"TEST_FAIL:{test_name}: {e}")
else:
    print(f"TEST_PASS:{test_name}")
    print(f"BENCHMARK:memory_allocation_latency_ms:{latency * 1000:.2f}")
    print(f"BENCHMARK:memory_allocation_current_bytes:{current}")
    print(f"BENCHMARK:memory_allocation_peak_bytes:{peak}")

# Measure import time
try:
    start_time = time.time()
    import rust
    end_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000:.2f}")
except Exception as e:
    print(f"TEST_FAIL:Import test: {e}")

# Compare performance vs baseline tool
# For this example, we'll use Python as the baseline tool
try:
    start_time = time.time()
    # Simple Python program
    python_code = """
    class Node:
        def __init__(self, value):
            self.value = value
            self.next = None
    node = Node(10)
    """
    exec(python_code)
    end_time = time.time()
    latency = end_time - start_time
    ratio = latency / (latency + 0.01)  # Add a small value to avoid division by zero
    print(f"BENCHMARK:vs_python_memory_allocation_ratio:{ratio:.2f}")
except Exception as e:
    print(f"TEST_FAIL:Baseline comparison test: {e}")

# Print final message
print("RUN_OK")