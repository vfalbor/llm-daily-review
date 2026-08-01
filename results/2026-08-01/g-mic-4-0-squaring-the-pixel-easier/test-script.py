import subprocess
import time
import tracemalloc
import importlib.util
import os

# Install required system packages
print("Installing required system packages...")
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Install gmic using pip
print("Installing gmic using pip...")
try:
    subprocess.run(['pip', 'install', 'gmic-python'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

    # Fallback installation using git clone and pip install -e .
    print("Falling back to git clone and pip install -e .")
    subprocess.run(['git', 'clone', 'https://github.com/dcmerchant/gmic.git'], check=True)
    subprocess.run(['pip', 'install', '-e', './gmic'], check=True, cwd='./gmic')
    print("INSTALL_OK")

# Import gmic and measure import time
print("Importing gmic and measuring import time...")
start_time = time.time()
import gmic
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time:.2f}")

# Run a basic gmic command
print("Running a basic gmic command...")
try:
    subprocess.run(['gmic', 'version'], check=True)
    print("TEST_PASS:gmic_version")
except Exception as e:
    print(f"TEST_FAIL:gmic_version:{str(e)}")

# Use gmic to convert an image to grayscale
print("Using gmic to convert an image to grayscale...")
try:
    subprocess.run(['gmic', 'input', 'image.jpg', 'convert', 'float', 'normalize', '0,100', 'to_grayscale', 'output', 'grayscale.jpg'], check=True)
    print("TEST_PASS:gmic_grayscale")
except Exception as e:
    print(f"TEST_FAIL:gmic_grayscale:{str(e)}")

# Measure performance of gmic vs ImageMagick
print("Measuring performance of gmic vs ImageMagick...")
try:
    # Install ImageMagick using apt
    subprocess.run(['apk', 'add', '--no-cache', 'imagemagick'], check=True)

    # Run gmic and ImageMagick commands to measure performance
    start_time = time.time()
    subprocess.run(['gmic', 'input', 'image.jpg', 'convert', 'float', 'normalize', '0,100', 'to_grayscale', 'output', 'grayscale_gmic.jpg'], check=True)
    end_time = time.time()
    gmic_time = (end_time - start_time) * 1000

    start_time = time.time()
    subprocess.run(['convert', 'image.jpg', '-colorspace', 'Gray', 'grayscale_imagemagick.jpg'], check=True)
    end_time = time.time()
    imagemagick_time = (end_time - start_time) * 1000

    print(f"BENCHMARK:gmic_grayscale_ms:{gmic_time:.2f}")
    print(f"BENCHMARK:imagemagick_grayscale_ms:{imagemagick_time:.2f}")
    print(f"BENCHMARK:vs_imagemagick_grayscale_ratio:{gmic_time / imagemagick_time:.2f}")
except Exception as e:
    print(f"TEST_FAIL:gmic_vs_imagemagick:{str(e)}")

# Measure memory usage
print("Measuring memory usage...")
tracemalloc.start()
import gmic
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Measure time to run a simple gmic command
print("Measuring time to run a simple gmic command...")
start_time = time.time()
subprocess.run(['gmic', 'version'], check=True)
end_time = time.time()
command_time = (end_time - start_time) * 1000
print(f"BENCHMARK:gmic_command_ms:{command_time:.2f}")

# Measure time to run a simple ImageMagick command
print("Measuring time to run a simple ImageMagick command...")
start_time = time.time()
subprocess.run(['convert', '-version'], check=True)
end_time = time.time()
command_time = (end_time - start_time) * 1000
print(f"BENCHMARK:imagemagick_command_ms:{command_time:.2f}")

print("RUN_OK")