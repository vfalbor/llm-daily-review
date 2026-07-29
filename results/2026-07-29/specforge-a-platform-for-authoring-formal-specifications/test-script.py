import subprocess
import time
import tracemalloc
import importlib
import sys

try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

try:
    subprocess.run(['pip', 'install', 'specforge'], check=True)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/imiron/specforge.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './specforge'], cwd='./specforge', check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

try:
    import specforge
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")

# Measure import time
start_time = time.time()
import specforge
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Measure editing time
start_time = time.time()
spec = specforge.Specification()
spec.add_statement("statement1")
spec.add_statement("statement2")
end_time = time.time()
editing_time = (end_time - start_time) * 1000
print(f"BENCHMARK:editing_time_ms:{editing_time}")

# Test minimal functionality
try:
    spec = specforge.Specification()
    spec.add_statement("statement1")
    spec.add_statement("statement2")
    print("TEST_PASS:specforge_functionality")
except Exception as e:
    print(f"TEST_FAIL:specforge_functionality:{e}")

# Compare with other formal specification editors
try:
    import spectacle
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/spectacle/spectacle.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './spectacle'], cwd='./spectacle', check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

try:
    import fsp
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL:{e}")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/fsp/fsp.git'], check=True)
        subprocess.run(['pip', 'install', '-e', './fsp'], cwd='./fsp', check=True)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL:{e}")

# Measure performance of SpecForge vs Spectacle
start_time = time.time()
spec = specforge.Specification()
spec.add_statement("statement1")
spec.add_statement("statement2")
end_time = time.time()
specforge_time = (end_time - start_time) * 1000

start_time = time.time()
spec = spectacle.Specification()
spec.add_statement("statement1")
spec.add_statement("statement2")
end_time = time.time()
spectacle_time = (end_time - start_time) * 1000

ratio = specforge_time / spectacle_time
print(f"BENCHMARK:vs_spectacle_editing_ratio:{ratio}")

# Measure performance of SpecForge vs FSP
start_time = time.time()
spec = specforge.Specification()
spec.add_statement("statement1")
spec.add_statement("statement2")
end_time = time.time()
specforge_time = (end_time - start_time) * 1000

start_time = time.time()
spec = fsp.Specification()
spec.add_statement("statement1")
spec.add_statement("statement2")
end_time = time.time()
fsp_time = (end_time - start_time) * 1000

ratio = specforge_time / fsp_time
print(f"BENCHMARK:vs_fsp_editing_ratio:{ratio}")

# Measure memory usage
tracemalloc.start()
spec = specforge.Specification()
spec.add_statement("statement1")
spec.add_statement("statement2")
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"BENCHMARK:memory_usage_bytes:{peak}")

# Measure test files count
files_count = len([name for name in subprocess.run(['git', 'ls-files'], capture_output=True, text=True).stdout.splitlines() if name.endswith('.py')])
print(f"BENCHMARK:test_files_count:{files_count}")

print("RUN_OK")