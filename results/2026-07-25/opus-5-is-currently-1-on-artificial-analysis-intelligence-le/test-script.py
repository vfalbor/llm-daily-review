import subprocess
import time
import tracemalloc
import importlib.util
import importlib.machinery

def run_test(name, func):
    try:
        func()
        print(f"TEST_PASS:{name}")
    except Exception as e:
        print(f"TEST_FAIL:{name}:{str(e)}")

def install_package(package_name):
    try:
        subprocess.run(['pip', 'install', package_name], check=True)
        print(f"INSTALL_OK")
    except subprocess.CalledProcessError as e:
        print(f"INSTALL_FAIL:{str(e)}")
        try:
            subprocess.run(['git', 'clone', f'https://github.com/{package_name}.git'], check=True)
            subprocess.run(['pip', 'install', '-e', './' + package_name], check=True)
            print(f"INSTALL_OK")
        except subprocess.CalledProcessError as e:
            print(f"INSTALL_FAIL:{str(e)}")

def measure_time(func):
    start_time = time.time()
    func()
    end_time = time.time()
    print(f"BENCHMARK:{func.__name__}_time_ms:{(end_time - start_time) * 1000}")

def compare_performance(baseline_tool, baseline_metric, metric_value):
    try:
        baseline_module = importlib.import_module(baseline_tool)
        baseline_func = getattr(baseline_module, baseline_metric)
        baseline_time = time.time()
        baseline_func()
        baseline_end_time = time.time()
        ratio = (metric_value / ((baseline_end_time - baseline_time) * 1000))
        print(f"BENCHMARK:vs_{baseline_tool}_{baseline_metric}_ratio:{ratio}")
    except Exception as e:
        print(f"BENCHMARK:vs_{baseline_tool}_{baseline_metric}_ratio:NA")

def main():
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    
    install_package('llm-ai')
    
    run_test('import_test', lambda: importlib.import_module('llm_ai'))
    
    import llm_ai
    
    tracemalloc.start()
    start_time = time.time()
    llm_ai_model = llm_ai.LLMModel()
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
    print(f"BENCHMARK:memory_usage_mb:{current / 10**6}")
    
    measure_time(lambda: llm_ai_model.predict('Hello World'))
    
    compare_performance('baseline_tool', 'baseline_predict', 100)

    print("RUN_OK")

if __name__ == '__main__':
    main()