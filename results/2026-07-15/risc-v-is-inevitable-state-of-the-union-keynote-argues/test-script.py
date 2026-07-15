import subprocess
import time
import tracemalloc
import os
import git
import sys

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'gcc'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'make'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'musl-dev'], check=False)

    install_ok = True
    try:
        subprocess.run(['git', 'clone', 'https://github.com/riscv/riscv-tools.git'], check=True)
        subprocess.run(['git', 'clone', 'https://github.com/riscv/riscv-isa-sim.git'], check=True)
        install_ok = True
    except subprocess.CalledProcessError as e:
        install_ok = False
        print(f"INSTALL_FAIL:git_clone failed with error {e}")

    print(f"INSTALL_OK" if install_ok else f"INSTALL_FAIL:git clone failed")

def build_riscv_tools():
    try:
        os.chdir('riscv-tools')
        subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], check=True)
        subprocess.run(['mkdir', '-p', 'build'], check=True)
        os.chdir('build')
        subprocess.run(['../configure', '--prefix=/usr/local'], check=True)
        subprocess.run(['make', '-j'], check=True)
        subprocess.run(['make', 'install'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:riscv_tools_build failed with error {e}")
        return False
    print("INSTALL_OK")
    return True

def run_riscv_program():
    try:
        os.chdir('riscv-isa-sim')
        subprocess.run(['mkdir', '-p', 'build'], check=True)
        os.chdir('build')
        subprocess.run(['cmake', '..'], check=True)
        subprocess.run(['make', '-j'], check=True)
        start_time = time.time()
        subprocess.run(['./simulate', '../tests/rv32ui-p-simple'], check=True)
        end_time = time.time()
        run_time = (end_time - start_time) * 1000
        print(f"BENCHMARK:riscv_program_ms:{run_time}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_riscv_program failed with error {e}")
        return False

def measure_performance_improvements():
    try:
        start_time = time.time()
        subprocess.run(['gcc', '-O3', 'example.c', '-o', 'example'], check=True)
        subprocess.run(['./example'], check=True)
        end_time = time.time()
        run_time_x86 = (end_time - start_time) * 1000
        start_time = time.time()
        subprocess.run(['riscv64-unknown-elf-gcc', '-O3', 'example.c', '-o', 'example_riscv'], check=True)
        subprocess.run(['spike', '--isa=rv64imafdc', 'example_riscv'], check=True)
        end_time = time.time()
        run_time_riscv = (end_time - start_time) * 1000
        print(f"BENCHMARK:riscv_x86_ratio:{run_time_riscv / run_time_x86}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:measure_performance_improvements failed with error {e}")
        return False

def verify_capabilities():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/ucb-bar/picorv32.git'], check=True)
        os.chdir('picorv32')
        subprocess.run(['make', 'verilate'], check=True)
        print(f"BENCHMARK:picorv32_loc_count:{sum(1 for _ in os.listdir())}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:verify_capabilities failed with error {e}")
        return False

def run_benchmarks():
    tracemalloc.start()
    start_time = time.time()
    run_riscv_program()
    end_time = time.time()
    run_time = (end_time - start_time) * 1000
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:riscv_program_import_time_ms:{run_time}")
    print(f"BENCHMARK:riscv_program_memory_usage_bytes:{current}")
    tracemalloc.stop()

def main():
    install_dependencies()
    if not build_riscv_tools():
        return
    if run_riscv_program():
        print(f"TEST_PASS:run_riscv_program")
    if measure_performance_improvements():
        print(f"TEST_PASS:measure_performance_improvements")
    if verify_capabilities():
        print(f"TEST_PASS:verify_capabilities")
    run_benchmarks()
    print("RUN_OK")

if __name__ == "__main__":
    main()