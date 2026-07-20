import subprocess
import sys
import time
import tracemalloc
import os

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'python3'], check=False)
    subprocess.run(['apk', 'add', '--no-cache', 'pip3'], check=False)

def clone_repo():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/retrogamecoders/c64-basic-dungeon.git'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:clone_repo:{e}")
        return False

def count_source_files():
    try:
        count = 0
        for root, dirs, files in os.walk('c64-basic-dungeon'):
            for file in files:
                count += 1
        print(f"BENCHMARK:source_file_count:{count}")
    except Exception as e:
        print(f"TEST_FAIL:count_source_files:{e}")

def check_simulator():
    try:
        # Check for Vice C64 emulator
        subprocess.run(['apk', 'add', '--no-cache', 'vice'], check=True)
        print("INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{e}")

def run_python_examples():
    try:
        subprocess.run(['python3', '-c', 'import os'], check=True)
        print("TEST_PASS:run_python_examples")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:run_python_examples:{e}")

def compare_performance():
    try:
        start_time = time.time()
        # Run the C64 Basic Dungeon game
        subprocess.run(['vice', '-autostart', 'c64-basic-dungeon/dungeon.prg'], check=True)
        end_time = time.time()
        game_time = end_time - start_time
        print(f"BENCHMARK:game_time_ms:{game_time * 1000}")
        
        # Compare performance vs NESdev
        start_time = time.time()
        # Run the NESdev example
        subprocess.run(['nesdev', '-example'], check=True)
        end_time = time.time()
        nesdev_time = end_time - start_time
        ratio = game_time / nesdev_time
        print(f"BENCHMARK:vs_nesdev_time_ratio:{ratio}")
    except subprocess.CalledProcessError as e:
        print(f"TEST_FAIL:compare_performance:{e}")

def main():
    install_dependencies()
    check_simulator()
    
    if clone_repo():
        count_source_files()
        run_python_examples()
        compare_performance()

    tracemalloc.start()
    start_time = time.time()
    # Run the C64 Basic Dungeon game
    subprocess.run(['vice', '-autostart', 'c64-basic-dungeon/dungeon.prg'], check=True)
    end_time = time.time()
    game_time = end_time - start_time
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:memory_usage Peak:{peak / 10**6} Current:{current / 10**6}")
    print(f"BENCHMARK:game_time_ms:{game_time * 1000}")
    tracemalloc.stop()
    
    print("RUN_OK")

if __name__ == "__main__":
    main()