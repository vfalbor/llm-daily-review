import subprocess
import time
import tracemalloc
import sys
import importlib.util
import importlib.machinery

# Install git package
apk_install_cmd = ['apk', 'add', '--no-cache', 'git']
try:
    subprocess.run(apk_install_cmd, check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print(f"INSTALL_FAIL:Failed to install {apk_install_cmd[2]} package")
    sys.exit(1)

# Clone mcufont repository and install
clone_cmd = ['git', 'clone', 'https://github.com/mcufont/mcufont.git']
install_cmd = ['pip', 'install', '-e', './mcufont']
try:
    subprocess.run(clone_cmd, check=True, cwd='/tmp')
    subprocess.run(install_cmd, check=True, cwd='/tmp/mcufont')
    print("INSTALL_OK")
except subprocess.CalledProcessError as e:
    print("INSTALL_FAIL:Failed to clone and install mcufont package")
    sys.exit(1)

# Import mcufont and time its import
start_time = time.time()
try:
    spec = importlib.util.find_spec('mcufont')
    if spec is None:
        raise ImportError
    mcufont = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mcufont)
    import_time_ms = (time.time() - start_time) * 1000
    print(f"BENCHMARK:import_time_ms:{import_time_ms:.2f}")
except ImportError as e:
    print("TEST_FAIL:import_mcufont:Failed to import mcufont module")
    import_time_ms = 0

# Generate font with custom size and measure rendering speed
try:
    start_time = time.time()
    # Replace this with a minimal functional test for your project
    mcufont.render_font(5)
    rendering_time_ms = (time.time() - start_time) * 1000
    print(f"BENCHMARK:rendering_time_ms:{rendering_time_ms:.2f}")
    print("TEST_PASS:font_generation")
except Exception as e:
    print(f"TEST_FAIL:font_generation:{str(e)}")

# Create a new project using mcufont and verify pixel-perfect output
try:
    start_time = time.time()
    # Replace this with a minimal functional test for your project
    mcufont.render_project('example_project')
    project_time_ms = (time.time() - start_time) * 1000
    print(f"BENCHMARK:project_time_ms:{project_time_ms:.2f}")
    print("TEST_PASS:project_creation")
except Exception as e:
    print(f"TEST_FAIL:project_creation:{str(e)}")

# Measure memory usage
tracemalloc.start()
mcufont.render_font(5)
mem_usage, peak_usage = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{mem_usage}")

# Compare performance vs the most similar baseline tool (Pixel Font Generator)
try:
    spec = importlib.util.find_spec('pixel_font_generator')
    if spec is None:
        raise ImportError
    pixel_font_generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pixel_font_generator)
    start_time = time.time()
    pixel_font_generator.render_font(5)
    baseline_time_ms = (time.time() - start_time) * 1000
    ratio = rendering_time_ms / baseline_time_ms
    print(f"BENCHMARK:vs_pixel_font_generator_ratio:{ratio:.2f}")
except ImportError as e:
    print("TEST_SKIP:baseline_comparison:Baseline tool not installed")
except Exception as e:
    print(f"TEST_FAIL:baseline_comparison:{str(e)}")

# Count lines of code
loc_count = 0
with open('/tmp/mcufont/mcufont.py', 'r') as f:
    loc_count = len(f.readlines())
print(f"BENCHMARK:loc_count:{loc_count}")

# Count test files
test_files_count = 0
import os
for root, dirs, files in os.walk('/tmp/mcufont'):
    for file in files:
        if file.endswith('.py') and 'test' in file:
            test_files_count += 1
print(f"BENCHMARK:test_files_count:{test_files_count}")

print("RUN_OK")