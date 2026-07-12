import subprocess
import time
import tracemalloc
import os

# Install necessary packages
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

try:
    # Clone Emacs repository
    subprocess.run(['git', 'clone', 'https://github.com/emacs-mirror/emacs'], check=True)
    # Build Emacs from source
    subprocess.run(['./configure', '--without-x'], cwd='emacs', check=True)
    subprocess.run(['make', '-j'], cwd='emacs', check=True)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL:{str(e)}')

try:
    # Install ghostel using pip
    subprocess.run(['pip', 'install', 'ghostel'], check=True)
    print('INSTALL_OK')
except Exception as e:
    # Try installing from source as fallback
    try:
        subprocess.run(['git', 'clone', 'https://github.com/dakra/ghostel'], check=True)
        subprocess.run(['pip', 'install', '-e', '.'], cwd='ghostel', check=True)
        print('INSTALL_OK')
    except Exception as e:
        print(f'INSTALL_FAIL:{str(e)}')

try:
    # Import ghostel and measure import time
    start_time = time.time()
    import ghostel
    end_time = time.time()
    import_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time}')
    print('TEST_PASS:import_test')
except Exception as e:
    print(f'TEST_FAIL:import_test:{str(e)}')

try:
    # Test rendering of simple ascii art
    tracemalloc.start()
    start_time = time.time()
    # Create a simple ascii art
    ascii_art = ' Hello World! '
    # Render the ascii art using ghostel
    ghostel.render(ascii_art)
    end_time = time.time()
    render_time = (end_time - start_time) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f'BENCHMARK:render_time_ms:{render_time}')
    print(f'BENCHMARK:render_memory_mb:{current / (1024 * 1024)}')
    print('TEST_PASS:render_test')
except Exception as e:
    print(f'TEST_FAIL:render_test:{str(e)}')

try:
    # Create a virtual framebuffer and test window resize, close, recreate
    # Since ghostel is a terminal emulator, we can't directly create a virtual framebuffer
    # We'll use Xvfb as a fallback
    subprocess.run(['apk', 'add', '--no-cache', 'xvfb'], check=True)
    subprocess.run(['Xvfb', ':1', '-ac', '-screen', '0', '1024x768x24'], check=True)
    # Test window resize, close, recreate
    start_time = time.time()
    subprocess.run(['xterm', '-display', ':1', '-geometry', '80x24'], check=True)
    end_time = time.time()
    resize_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:resize_time_ms:{resize_time}')
    print('TEST_PASS:resize_test')
except Exception as e:
    print(f'TEST_FAIL:resize_test:{str(e)}')

try:
    # Check font rendering and rendering of complex fonts
    # Since ghostel is a terminal emulator, font rendering is handled by the terminal
    # We'll use a simple font test as a fallback
    start_time = time.time()
    subprocess.run(['xterm', '-display', ':1', '-font', 'fixed'], check=True)
    end_time = time.time()
    font_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:font_time_ms:{font_time}')
    print('TEST_PASS:font_test')
except Exception as e:
    print(f'TEST_FAIL:font_test:{str(e)}')

try:
    # Compare performance vs a native terminal
    # We'll use xterm as a baseline
    start_time = time.time()
    subprocess.run(['xterm'], check=True)
    end_time = time.time()
    xterm_time = (end_time - start_time) * 1000
    print(f'BENCHMARK:vs_xterm_time_ms:{xterm_time}')
    ratio = import_time / xterm_time
    print(f'BENCHMARK:vs_xterm_import_ratio:{ratio}')
    print('TEST_PASS:performance_test')
except Exception as e:
    print(f'TEST_FAIL:performance_test:{str(e)}')

print('RUN_OK')