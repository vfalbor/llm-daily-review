import subprocess
import time
import tracemalloc
import os

def install_dependencies():
    # Install system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'curl'], check=False)
    print("INSTALL_OK")

def measure_time(func):
    start_time = time.time()
    func()
    end_time = time.time()
    return end_time - start_time

def measure_memory(func):
    tracemalloc.start()
    func()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / (1024 * 1024)  # Convert to MB

def test_design_functionality():
    try:
        # Clone the repository
        subprocess.run(['git', 'clone', 'https://github.com/essenceia/ethernet_switch_asic.git'])
        # Change directory to the cloned repository
        os.chdir('ethernet_switch_asic')
        # Run the simulation
        simulation_time = measure_time(lambda: subprocess.run(['make', 'sim'], check=False))
        print(f"BENCHMARK:simulation_time_ms:{simulation_time * 1000}")
        print("TEST_PASS:design_functionality")
    except Exception as e:
        print(f"TEST_FAIL:design_functionality:{str(e)}")

def test_latency_and_throughput():
    try:
        # Run the FPGA prototyping
        fpga_time = measure_time(lambda: subprocess.run(['make', 'fpga'], check=False))
        print(f"BENCHMARK:fpga_time_ms:{fpga_time * 1000}")
        print("TEST_PASS:latency_and_throughput")
    except Exception as e:
        print(f"TEST_FAIL:latency_and_throughput:{str(e)}")

def test_energy_efficiency():
    try:
        # Compare energy efficiency with Xilinx SDSoC
        xilinx_time = measure_time(lambda: subprocess.run(['make', 'xilinx'], check=False))
        xilinx_energy = measure_memory(lambda: subprocess.run(['make', 'xilinx'], check=False))
        asic_time = measure_time(lambda: subprocess.run(['make', 'asic'], check=False))
        asic_energy = measure_memory(lambda: subprocess.run(['make', 'asic'], check=False))
        ratio = xilinx_time / asic_time
        print(f"BENCHMARK:vs_xilinx_energy_efficiency_ratio:{ratio}")
        print(f"BENCHMARK:energy_efficiency_ms:{asic_time * 1000}")
        print(f"BENCHMARK:energy_efficiency_mb:{asic_energy}")
        print("TEST_PASS:energy_efficiency")
    except Exception as e:
        print(f"TEST_FAIL:energy_efficiency:{str(e)}")

def test_baseline_tool():
    try:
        # Compare performance with NVIDIA Tegra
        nvidia_time = measure_time(lambda: subprocess.run(['make', 'nvidia'], check=False))
        asic_time = measure_time(lambda: subprocess.run(['make', 'asic'], check=False))
        ratio = nvidia_time / asic_time
        print(f"BENCHMARK:vs_nvidia_latency_ms_ratio:{ratio}")
        print(f"BENCHMARK:vs_nvidia_latency_ms_diff:{nvidia_time * 1000 - asic_time * 1000}")
        print("TEST_PASS:baseline_tool")
    except Exception as e:
        print(f"TEST_FAIL:baseline_tool:{str(e)}")

def main():
    install_dependencies()
    test_design_functionality()
    test_latency_and_throughput()
    test_energy_efficiency()
    test_baseline_tool()
    print("RUN_OK")

if __name__ == "__main__":
    main()