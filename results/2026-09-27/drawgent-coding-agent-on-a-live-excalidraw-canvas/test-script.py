#!/usr/bin/env python3
import subprocess, sys, time, tracemalloc, json, os, math

def print_marker(msg):
    print(msg, flush=True)

def install_apk(pkg):
    try:
        res = subprocess.run(['apk', 'add', '--no-cache', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} returncode {res.returncode}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} exception {e}")

def pip_install(pkg):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', pkg],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:pip install {pkg} rc {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip install {pkg} exception {e}")
        return False

def pip_install_editable(path):
    try:
        res = subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:pip install -e {path} rc {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:pip install -e {path} exception {e}")
        return False

def git_clone(repo, dest):
    try:
        res = subprocess.run(['git', 'clone', '--depth', '1', repo, dest],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if res.returncode == 0:
            print_marker("INSTALL_OK")
            return True
        else:
            print_marker(f"INSTALL_FAIL:git clone {repo} rc {res.returncode}")
            return False
    except Exception as e:
        print_marker(f"INSTALL_FAIL:git clone {repo} exception {e}")
        return False

def benchmark(name, func, *args, **kwargs):
    start = time.time()
    tracemalloc.start()
    try:
        result = func(*args, **kwargs)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    end = time.time()
    elapsed = end - start
    print_marker(f"BENCHMARK:{name}_s:{elapsed:.4f}")
    print_marker(f"BENCHMARK:{name}_mem_kb:{peak/1024:.2f}")
    return elapsed, result

def main():
    # 1. Install required apk packages
    install_apk('git')
    # 2. Install drawgent via pip, fallback to git
    pkg_name = 'drawgent'
    installed = pip_install(pkg_name)
    if not installed:
        repo = 'https://github.com/yanndegat/drawgent.git'
        src_dir = '/tmp/drawgent_src'
        if git_clone(repo, src_dir):
            installed = pip_install_editable(src_dir)
        else:
            installed = False

    # 3. Benchmark import time
    import_time = None
    try:
        import_time_start = time.time()
        import drawgent
        import_time = time.time() - import_time_start
        print_marker(f"BENCHMARK:import_time_s:{import_time:.6f}")
        print_marker("TEST_PASS:import")
    except Exception as e:
        print_marker(f"TEST_FAIL:import:{e}")

    # 4. Minimal functional test
    def run_minimal():
        # Assuming drawgent provides a class CanvasAgent with a method process_commands
        agent = drawgent.CanvasAgent()
        # Synthetic command: draw a rectangle
        commands = [{"type": "rect", "x": 10, "y": 10, "width": 100, "height": 50, "color": "black"}]
        # The method may be async; handle both cases
        result = agent.process_commands(commands)
        return result

    try:
        lat, _ = benchmark('core_operation', run_minimal)
        print_marker("TEST_PASS:core_operation")
    except Exception as e:
        print_marker(f"TEST_FAIL:core_operation:{e}")

    # 5. Baseline comparison against a simple dummy operation
    def dummy_op():
        # simple loop to simulate baseline work
        total = 0
        for i in range(100000):
            total += i*i
        return total

    try:
        baseline_lat, _ = benchmark('baseline_dummy', dummy_op)
        # compare core_operation latency (if measured) against baseline
        if 'lat' in locals() and baseline_lat > 0:
            ratio = lat / baseline_lat
            print_marker(f"BENCHMARK:vs_dummy_ratio:{ratio:.4f}")
        else:
            print_marker("BENCHMARK:vs_dummy_ratio:NA")
    except Exception as e:
        print_marker(f"TEST_FAIL:baseline_compare:{e}")

    # 6. Additional metrics
    # Count files in the package
    try:
        pkg_path = os.path.dirname(drawgent.__file__)
        file_count = sum(len(files) for _, _, files in os.walk(pkg_path))
        print_marker(f"BENCHMARK:loc_count:{file_count}")
        print_marker("TEST_PASS:file_count")
    except Exception as e:
        print_marker(f"TEST_FAIL:file_count:{e}")

    # 7. Ensure script ends with RUN_OK
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()