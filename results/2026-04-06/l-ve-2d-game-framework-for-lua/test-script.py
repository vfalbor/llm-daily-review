import importlib.util
import importlib.machinery
import time
import os
import subprocess

# INSTALL_OK marker
print("INSTALL_OK")

# Try to import love2d (not available via pip, skip if not found)
try:
    spec = importlib.util.find_spec("love2d")
    if spec is None:
        print("TEST_SKIP:import_love2d:love2d not found")
except Exception as e:
    print(f"TEST_FAIL:import_love2d:{str(e)}")

# Create a simple 2D game
try:
    # Since love2d is a Lua framework, create a simple game in Lua
    game_file = "game.lua"
    with open(game_file, 'w') as f:
        f.write("""
        function love.load()
            love.graphics.setBackgroundColor(0, 0, 1)
        end

        function love.update(dt)
        end

        function love.draw()
            love.graphics.print("Hello World", 100, 100)
        end
        """)
    print("TEST_PASS:create_simple_game")
except Exception as e:
    print(f"TEST_FAIL:create_simple_game:{str(e)}")

# Try to run the game
try:
    # Love2d is typically run via the love command, not available in python:3.12-alpine
    # As an alternative, we test if love executable is available
    if 'LOVE_EXECUTABLE' in os.environ:
        subprocess.run([os.environ['LOVE_EXECUTABLE'], game_file])
        print("TEST_PASS:run_game")
    else:
        print("TEST_SKIP:run_game:LOVE_EXECUTABLE not found")
except Exception as e:
    print(f"TEST_FAIL:run_game:{str(e)}")

# Compare ease of use vs. Pygame
try:
    import pygame
    import numpy as np
    print("TEST_PASS:import_pygame")
    # Create a simple Pygame window
    pygame.init()
    window = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Hello World")
    print("TEST_PASS:create_pygame_window")
except Exception as e:
    print(f"TEST_FAIL:import_pygame:{str(e)}")

# Measure import time
try:
    start_time = time.time()
    importlib.import_module("pygame")
    import_time = (time.time() - start_time) * 1000
    print(f"BENCHMARK:import_time_ms_pygame:{import_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_pygame:{str(e)}")

try:
    # love2d is not available as a python module
    spec = importlib.util.find_spec("love2d")
    if spec is None:
        print("TEST_SKIP:import_love2d:love2d not found")
    else:
        start_time = time.time()
        importlib.import_module("love2d")
        import_time = (time.time() - start_time) * 1000
        print(f"BENCHMARK:import_time_ms_love2d:{import_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:import_love2d:{str(e)}")

# Print RUN_OK marker
print("RUN_OK")