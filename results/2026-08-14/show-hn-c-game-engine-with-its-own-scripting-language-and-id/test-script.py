import subprocess
import time
import tracemalloc
import importlib.util

# Install git package
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print('INSTALL_OK')

try:
    # Install ArcadeMaker package
    subprocess.run(['pip', 'install', 'git+https://github.com/ArcadeMakerSources/ArcadeMaker.git'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')
    try:
        # Clone the repo
        subprocess.run(['git', 'clone', 'https://github.com/ArcadeMakerSources/ArcadeMaker.git'], check=False)
        # Install from source
        subprocess.run(['pip', 'install', '-e', './ArcadeMaker'], check=False, cwd='./ArcadeMaker')
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

# Import the package
try:
    module_spec = importlib.util.find_spec('arcademaker')
    if module_spec is None:
        raise ImportError
    importlib.util.module_from_spec(module_spec)
    print('TEST_PASS:import_arcademaker')
except Exception as e:
    print(f'TEST_FAIL:import_arcademaker:{str(e)}')

# Measure import time
start_time = time.time()
try:
    import arcademaker
    import_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time:.2f}')
except Exception as e:
    print(f'TEST_FAIL:arcademaker_import_time:{str(e)}')

# Measure core operation latency
start_time = time.time()
try:
    # Create a simple game
    game = arcademaker.Game()
    game.update()
    operation_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:core_operation_latency_ms:{operation_time:.2f}')
    print('TEST_PASS:simple_game_creation')
except Exception as e:
    print(f'TEST_FAIL:simple_game_creation:{str(e)}')

# Measure memory usage
tracemalloc.start()
try:
    import arcademaker
    current, peak = tracemalloc.get_traced_memory()
    print(f'BENCHMARK:memory_usage_bytes:{current}')
    tracemalloc.stop()
except Exception as e:
    print(f'TEST_FAIL:memory_usage:{str(e)}')

# Compare performance vs Unity (similar baseline tool)
try:
    import unitypy
    start_time = time.time()
    unitypy.Game()
    unity_import_time = (time.time() - start_time) * 1000
    ratio = import_time / unity_import_time
    print(f'BENCHMARK:vs_unity_import_time_ratio:{ratio:.2f}')
except Exception as e:
    print(f'TEST_FAIL:unity_comparison:{str(e)}')

# Additional tests
try:
    # Clone the repo and build a simple game from source
    subprocess.run(['git', 'clone', 'https://github.com/ArcadeMakerSources/ArcadeMaker.git'], check=False)
    subprocess.run(['dotnet', 'build'], check=False, cwd='./ArcadeMaker')
    print('TEST_PASS:build_simple_game')
except Exception as e:
    print(f'TEST_FAIL:build_simple_game:{str(e)}')

try:
    # Run the game and verify correct output
    subprocess.run(['dotnet', 'run'], check=False, cwd='./ArcadeMaker')
    print('TEST_PASS:run_game')
except Exception as e:
    print(f'TEST_FAIL:run_game:{str(e)}')

print('RUN_OK')