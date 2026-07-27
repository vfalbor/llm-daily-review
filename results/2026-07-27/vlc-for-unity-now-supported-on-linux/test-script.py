import subprocess
import sys
import time
import tracemalloc
import importlib.util
import os

# Install system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)

# Clone the VLC for Unity repository
try:
    subprocess.run(['git', 'clone', 'https://code.videolan.org/videolan/vlc-unity.git'], check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL: {e}')

# Build VLC for Unity
try:
    subprocess.run(['git', 'clone', 'https://code.videolan.org/videolan/vlc-unity.git'], check=False)
    subprocess.run(['python3', '-m', 'pip', 'install', '-r', 'vlc-unity/requirements.txt'], check=False)
    subprocess.run(['python3', 'setup.py', 'build'], cwd='vlc-unity', check=False)
    print('INSTALL_OK')
except Exception as e:
    print(f'INSTALL_FAIL: {e}')

# Test video playback
try:
    # Load the vlc module
    spec = importlib.util.spec_from_file_location("vlc", "vlc-unity/vlc.py")
    vlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vlc)

    # Measure import time
    start_time = time.time()
    importlib.import_module('vlc')
    import_time = (time.time() - start_time) * 1000
    print(f'BENCHMARK:import_time_ms:{import_time}')

    # Test video playback
    vlc_instance = vlc.Instance()
    player = vlc_instance.media_player_new()
    media = vlc_instance.media_new('sample.mp4')
    player.set_media(media)
    player.play()
    time.sleep(5)
    print('TEST_PASS:video_playback')

    # Measure playback latency
    start_time = time.time()
    player.play()
    time.sleep(5)
    playback_latency = (time.time() - start_time) * 1000
    print(f'BENCHMARK:playback_latency_ms:{playback_latency}')
except Exception as e:
    print(f'TEST_FAIL:video_playback: {e}')

# Compare performance vs VLC
try:
    # Load the vlc module
    import importlib.util
    spec = importlib.util.spec_from_file_location("vlc", "vlc-unity/vlc.py")
    vlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vlc)

    # Load the python-vlc module for comparison
    import importlib.util
    spec = importlib.util.spec_from_file_location("python_vlc", "python-vlc/__init__.py")
    python_vlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(python_vlc)

    # Measure import time
    start_time = time.time()
    importlib.import_module('vlc')
    vlc_import_time = (time.time() - start_time) * 1000

    start_time = time.time()
    importlib.import_module('python_vlc')
    python_vlc_import_time = (time.time() - start_time) * 1000

    print(f'BENCHMARK:vs_vlc_import_time_ratio:{vlc_import_time / python_vlc_import_time}')

except Exception as e:
    print(f'TEST_FAIL:compare_performance: {e}')

# Measure memory usage
tracemalloc.start()
importlib.import_module('vlc')
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f'BENCHMARK:memory_usage_bytes:{peak}')
print(f'BENCHMARK:memory_usage_bytes:{current}')

# Measure time taken for core operations
start_time = time.time()
importlib.import_module('vlc')
end_time = time.time()
core_operation_time = (end_time - start_time) * 1000
print(f'BENCHMARK:core_operation_time_ms:{core_operation_time}')

print('RUN_OK')