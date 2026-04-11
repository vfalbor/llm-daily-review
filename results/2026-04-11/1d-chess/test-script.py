import os
import subprocess
import sys
import time
import tracemalloc
import importlib.util
import importlib.machinery
from io import StringIO
import contextlib

# Install system packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install git - {e}")
    sys.exit(1)

print("INSTALL_OK")

# Clone the repository and install the package
try:
    subprocess.run(['git', 'clone', 'https://github.com/rowan441/1dchess.git'], check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to clone the repository - {e}")
    sys.exit(1)

try:
    subprocess.run(['pip', 'install', '-e', './1dchess'], cwd='./1dchess', check=True)
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install the package - {e}")
    sys.exit(1)

print("INSTALL_OK")

# Import the module
try:
    spec = importlib.util.spec_from_file_location("one_d_chess", "./1dchess/one_d_chess.py")
    one_d_chess = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(one_d_chess)
except ImportError as e:
    print(f"TEST_FAIL:Import - {e}")
    print("RUN_OK")
    sys.exit(1)

# Measure import time
import_time = time.time()
importlib.import_module("one_d_chess")
import_time = time.time() - import_time
print(f"BENCHMARK:import_time_ms:{import_time*1000:.2f}")

# Measure core operation latency
tracemalloc.start()
start_time = time.time()
one_d_chess.start_game()
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:core_operation_latency_ms:{(end_time-start_time)*1000:.2f}")
print(f"BENCHMARK:core_operation_memory_mb:{peak/1024/1024:.2f}")

# Measure input lag
start_time = time.time()
one_d_chess.handle_input("1")
end_time = time.time()
print(f"BENCHMARK:input_lag_ms:{(end_time-start_time)*1000:.2f}")

# Compare with classic Chess
try:
    import chess
except ImportError as e:
    print(f"TEST_FAIL:Compare with classic Chess - {e}")
    print("RUN_OK")
    sys.exit(1)

# Measure time to make a move in classic Chess
start_time = time.time()
board = chess.Board()
board.push_uci("e2e4")
end_time = time.time()
print(f"BENCHMARK:classic_chess_move_time_ms:{(end_time-start_time)*1000:.2f}")

# Compare performance
classic_chess_time = end_time - start_time
one_d_chess_time = current
print(f"BENCHMARK:vs_classic_chess_move_ratio:{(one_d_chess_time/classic_chess_time):.2f}")

print("RUN_OK")