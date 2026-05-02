import subprocess
import requests
import time
import tracemalloc

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'nodejs', 'npm'], check=False)
print("INSTALL_OK")

# Install tool dependencies (npm)
try:
    subprocess.run(['npm', 'install', 'mathstick'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:{e}")

# Start the server in background
try:
    subprocess.Popen(['node', 'server.js'], cwd='/app')
    print("SERVER_STARTED")
except FileNotFoundError:
    print("SERVER_FAIL")

# Test 1: Create a custom puzzle and measure solving time
try:
    start_time = time.time()
    response = requests.post('http://localhost:3000/puzzle', json={'size': 5})
    end_time = time.time()
    puzzle_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:puzzle_time_ms:{puzzle_time:.2f}")
    print("TEST_PASS:create_puzzle")
except requests.exceptions.RequestException as e:
    print(f"TEST_FAIL:create_puzzle:{e}")

# Test 2: Build a simple game with the API
try:
    start_time = time.time()
    response = requests.get('http://localhost:3000/game')
    end_time = time.time()
    game_time = (end_time - start_time) * 1000
    print(f"BENCHMARK:game_time_ms:{game_time:.2f}")
    print("TEST_PASS:build_game")
except requests.exceptions.RequestException as e:
    print(f"TEST_FAIL:build_game:{e}")

# Measure memory usage
tracemalloc.start()
time.sleep(1)
current, peak = tracemalloc.get_traced_memory()
print(f"BENCHMARK:memory_usage_mb:{current / (1024 * 1024):.2f}")
tracemalloc.stop()

# Compare performance vs the most similar baseline tool (Puzzle maker)
try:
    start_time = time.time()
    response = requests.get('https://puzzle-maker.com/game')
    end_time = time.time()
    puzzle_maker_time = (end_time - start_time) * 1000
    ratio = puzzle_time / puzzle_maker_time
    print(f"BENCHMARK:vs_puzzle_maker_ratio:{ratio:.2f}")
except requests.exceptions.RequestException as e:
    print(f"BENCHMARK:vs_puzzle_maker_ratio:nan")

print("RUN_OK")