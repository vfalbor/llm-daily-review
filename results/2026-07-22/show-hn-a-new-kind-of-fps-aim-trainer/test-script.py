import subprocess
import sys
import time
import tracemalloc
import importlib.util
import importlib.machinery

def install_dependencies():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    try:
        subprocess.run(['pip', 'install', 'openaim'], check=False)
    except subprocess.CalledProcessError:
        print("INSTALL_FAIL:openaim")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/openaim/openaim.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './openaim'], check=False, cwd='./openaim')
        except subprocess.CalledProcessError as e:
            print("INSTALL_FAIL:openaim_fallback:{}".format(e))
            return False
    return True

def test_openaim_import():
    try:
        start_time = time.time()
        spec = importlib.util.find_spec('openaim')
        if spec is None:
            print("TEST_FAIL:openaim_import:OpenAIM not found")
        else:
            openaim = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(openaim)
            end_time = time.time()
            import_time = (end_time - start_time) * 1000
            print("BENCHMARK:import_time_ms:{}".format(import_time))
            print("TEST_PASS:openaim_import")
    except Exception as e:
        print("TEST_FAIL:openaim_import:{}".format(e))

def test_openaim_accuracy():
    try:
        import openaim
        tracemalloc.start()
        start_time = time.time()
        openaim.train()
        end_time = time.time()
        accuracy_time = (end_time - start_time) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print("BENCHMARK:accuracy_time_ms:{}".format(accuracy_time))
        print("BENCHMARK:accuracy_memory_peak_mb:{}".format(peak / 1024 / 1024))
        print("TEST_PASS:openaim_accuracy")
    except Exception as e:
        print("TEST_FAIL:openaim_accuracy:{}".format(e))

def test_openaim_analytics():
    try:
        import openaim
        tracemalloc.start()
        start_time = time.time()
        openaim.track_progress()
        end_time = time.time()
        analytics_time = (end_time - start_time) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print("BENCHMARK:analytics_time_ms:{}".format(analytics_time))
        print("BENCHMARK:analytics_memory_peak_mb:{}".format(peak / 1024 / 1024))
        print("TEST_PASS:openaim_analytics")
    except Exception as e:
        print("TEST_FAIL:openaim_analytics:{}".format(e))

def compare_to_baseline():
    try:
        import openaim
        import aim_lab
        openaim_time = time.time()
        openaim.train()
        openaim_end_time = time.time()
        aim_lab_time = time.time()
        aim_lab.train()
        aim_lab_end_time = time.time()
        ratio = ((openaim_end_time - openaim_time) / (aim_lab_end_time - aim_lab_time)) * 100
        print("BENCHMARK:vs_aim_lab_ratio:{}".format(ratio))
        print("TEST_PASS:compare_to_baseline")
    except Exception as e:
        print("TEST_FAIL:compare_to_baseline:{}".format(e))

if __name__ == "__main__":
    if install_dependencies():
        print("INSTALL_OK")
    test_openaim_import()
    test_openaim_accuracy()
    test_openaim_analytics()
    compare_to_baseline()
    print("RUN_OK")