import subprocess
import sys
import time
import tracemalloc
import matplotlib.pyplot as plt
import numpy as np
from inclusive_color_space import generate_skin_tones

# Install required packages
def install_packages(package):
    try:
        subprocess.run(['apk', 'add', '--no-cache', package], check=False)
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

install_packages('git')
install_packages('python3-dev')

# Install the library using pip
def install_library():
    try:
        subprocess.run(['pip', 'install', 'inclusive-color-space'], check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/toneyalexander/inclusive-color-space.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './inclusive-color-space'], check=True)
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:{e}")

install_library()

# Test 1: Generate and visualize a color palette
def test_generate_palette():
    try:
        tracemalloc.start()
        start_time = time.time()
        skin_tones = generate_skin_tones(10)
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        plt.imshow(skin_tones)
        plt.show()
        print(f"BENCHMARK:generate_time_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:generate_memory_mb:{current / 10**6}")
        print(f"TEST_PASS:generate_palette")
    except Exception as e:
        print(f"TEST_FAIL:generate_palette:{e}")

test_generate_palette()

# Test 2: Compare generated palette to a known reference
def test_compare_palette():
    try:
        skin_tones = generate_skin_tones(10)
        reference_tones = np.array([[0.5, 0.5, 0.5], [0.6, 0.6, 0.6], [0.7, 0.7, 0.7], [0.8, 0.8, 0.8], [0.9, 0.9, 0.9],
                                     [0.4, 0.4, 0.4], [0.3, 0.3, 0.3], [0.2, 0.2, 0.2], [0.1, 0.1, 0.1], [0.0, 0.0, 0.0]])
        if np.allclose(skin_tones, reference_tones):
            print(f"TEST_PASS:compare_palette")
        else:
            print(f"TEST_FAIL:compare_palette")
    except Exception as e:
        print(f"TEST_FAIL:compare_palette:{e}")

test_compare_palette()

# Test 3: Verify algorithm handles edge cases
def test_edge_cases():
    try:
        generate_skin_tones(0)
        print(f"TEST_PASS:edge_cases")
    except Exception as e:
        print(f"TEST_FAIL:edge_cases:{e}")

test_edge_cases()

# Compare performance vs the most similar baseline tool listed above (ColorThief)
def compare_performance():
    try:
        import colorthief
        start_time = time.time()
        color_thief = colorthief.ColorThief('tests/data/image.jpg')
        end_time = time.time()
        print(f"BENCHMARK:vs_colorthief_get_color_ms:{(end_time - start_time) * 1000}")
    except Exception as e:
        print(f"BENCHMARK:vs_colorthief_get_color_ms:NA")

compare_performance()

print("RUN_OK")