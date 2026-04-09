import subprocess
import time
import tracemalloc
import os

def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_command:{e}")
        return False
    return True

def main():
    # Install system packages
    print("INSTALLING SYSTEM PACKAGES...")
    install_commands = [
        ['apk', 'add', '--no-cache', 'git'],
        ['pip', 'install', 'scapy']  # For creating synthetic packets
    ]
    for command in install_commands:
        if not run_command(command):
            print("INSTALL_FAIL:system_packages")
            return

    # Install LittleSnitch (assuming pip package)
    print("INSTALLING LITTLESNITCH...")
    install_commands = [
        ['pip', 'install', 'littlesnitch']
    ]
    for command in install_commands:
        try:
            subprocess.run(command, check=True)
            print("INSTALL_OK")
            break
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:LittleSnitch:{e}")
            # Fallback to git clone + pip install -e .
            try:
                subprocess.run(['git', 'clone', 'https://github.com/Obdev/LittleSnitch.git'], check=True)
                subprocess.run(['pip', 'install', '-e', 'LittleSnitch'], check=True)
                print("INSTALL_OK")
            except subprocess.CalledProcessError as e:
                print(f"INSTALL_FAIL:LittleSnitch:{e}")
                return

    # Run tests
    print("RUNNING TESTS...")
    test_names = [
        'test_import_time',
        'test_core_operation_latency',
        'test_synthetic_packet',
        'test_custom_packet_flow',
        'test_vs_native_linux_firewall'
    ]

    for test_name in test_names:
        try:
            if test_name == 'test_import_time':
                import_time = time.time()
                import littlesnitch
                import_time_ms = (time.time() - import_time) * 1000
                print(f"BENCHMARK:import_time_ms:{import_time_ms}")
                print(f"TEST_PASS:{test_name}")

            elif test_name == 'test_core_operation_latency':
                import littlesnitch
                start_time = time.time()
                # Create a synthetic packet using scapy
                from scapy.all import IP, TCP, Raw
                packet = IP(dst="8.8.8.8") / TCP(dport=80) / Raw("Hello, world!")
                littlesnitch.filter_packet(packet)
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                print(f"BENCHMARK:core_operation_latency_ms:{latency_ms}")
                print(f"TEST_PASS:{test_name}")

            elif test_name == 'test_synthetic_packet':
                import littlesnitch
                from scapy.all import IP, TCP, Raw
                packet = IP(dst="8.8.8.8") / TCP(dport=80) / Raw("Hello, world!")
                littlesnitch.filter_packet(packet)
                print(f"TEST_PASS:{test_name}")

            elif test_name == 'test_custom_packet_flow':
                import littlesnitch
                from scapy.all import IP, TCP, Raw
                # Create a custom packet flow
                packet1 = IP(dst="8.8.8.8") / TCP(dport=80) / Raw("Hello, world!")
                packet2 = IP(dst="8.8.8.8") / TCP(dport=80) / Raw("This is a custom packet flow")
                littlesnitch.filter_packet(packet1)
                littlesnitch.filter_packet(packet2)
                print(f"TEST_PASS:{test_name}")

            elif test_name == 'test_vs_native_linux_firewall':
                import littlesnitch
                import time
                # Measure time taken by LittleSnitch to filter a packet
                start_time = time.time()
                from scapy.all import IP, TCP, Raw
                packet = IP(dst="8.8.8.8") / TCP(dport=80) / Raw("Hello, world!")
                littlesnitch.filter_packet(packet)
                end_time = time.time()
                littlesnitch_time_ms = (end_time - start_time) * 1000

                # Measure time taken by native Linux firewall to filter a packet
                start_time = time.time()
                # Use iptables to filter the packet
                subprocess.run(['iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', '80', '-j', 'DROP'], check=True)
                end_time = time.time()
                native_time_ms = (end_time - start_time) * 1000

                ratio = littlesnitch_time_ms / native_time_ms
                print(f"BENCHMARK:vs_native_linux_firewall_ratio:{ratio}")
                print(f"TEST_PASS:{test_name}")

            else:
                print(f"TEST_SKIP:{test_name}:Unknown test")

        except Exception as e:
            print(f"TEST_FAIL:{test_name}:{e}")

    # Measure memory usage
    tracemalloc.start()
    import littlesnitch
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")
    tracemalloc.stop()

    # Measure count of test files
    test_files_count = len(os.listdir('tests'))
    print(f"BENCHMARK:test_files_count:{test_files_count}")

    # Measure count of lines of code
    loc_count = 0
    for root, dirs, files in os.walk('littlesnitch'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r') as f:
                    loc_count += len(f.readlines())
    print(f"BENCHMARK:loc_count:{loc_count}")

    print("RUN_OK")

if __name__ == "__main__":
    main()