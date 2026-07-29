import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

# Install required system packages
subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
print("INSTALL_OK")

# Install the Hubble package using pip
try:
    subprocess.run(['pip', 'install', 'hubble'], check=True)
    print("INSTALL_OK")
except subprocess.CalledProcessError:
    print("INSTALL_FAIL:Failed to install using pip, trying git install")
    subprocess.run(['git', 'clone', 'https://github.com/hubble-notetaking/note.git'], check=True)
    subprocess.run(['pip', 'install', '-e', 'note'], check=True)
    print("INSTALL_OK")

# Import the Hubble package and measure import time
start_time = time.time()
spec = importlib.util.find_spec('hubble')
if spec is None:
    print("TEST_FAIL:hubble_import:Failed to import hubble")
else:
    hubble = importlib.import_module('hubble')
end_time = time.time()
import_time = (end_time - start_time) * 1000  # convert to ms
print(f"BENCHMARK:import_time_ms:{import_time}")

# Create a new notebook and measure creation time
start_time = time.time()
try:
    notebook = hubble.Notebook()
    notebook.create_note("Test Note")
    end_time = time.time()
    creation_time = (end_time - start_time) * 1000  # convert to ms
    print(f"TEST_PASS:create_notebook")
    print(f"BENCHMARK:create_notebook_ms:{creation_time}")
except Exception as e:
    print(f"TEST_FAIL:create_notebook:{str(e)}")

# Run a minimal functional test with synthetic data
start_time = time.time()
try:
    notebook.add_note("Test Note 2")
    end_time = time.time()
    add_note_time = (end_time - start_time) * 1000  # convert to ms
    print(f"TEST_PASS:add_note")
    print(f"BENCHMARK:add_note_ms:{add_note_time}")
except Exception as e:
    print(f"TEST_FAIL:add_note:{str(e)}")

# Compare performance vs Simplenote
try:
    subprocess.run(['pip', 'install', 'simplenote'], check=True)
    import simplenote
    start_time = time.time()
    simplenote_notebook = simplenote.Notebook()
    simplenote_notebook.create_note("Test Note")
    end_time = time.time()
    simplenote_creation_time = (end_time - start_time) * 1000  # convert to ms
    ratio = creation_time / simplenote_creation_time
    print(f"BENCHMARK:vs_simplenote_create_notebook_ratio:{ratio}")
except Exception as e:
    print(f"TEST_SKIP:compare_simplenote:{str(e)}")

# Measure memory usage
tracemalloc.start()
notebook.get_notes()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_mb:{current / (1024 * 1024)}")
print(f"BENCHMARK:peak_memory_usage_mb:{peak / (1024 * 1024)}")

print("RUN_OK")