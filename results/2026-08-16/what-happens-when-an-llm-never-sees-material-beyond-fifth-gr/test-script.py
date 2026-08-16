import subprocess
import importlib.util
import importlib.machinery
import time
import tracemalloc
import os

def install_dependencies():
    print("Installing dependencies...")
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    try:
        subprocess.run(['pip', 'install', 'llm-fifth-grade-only'], check=False)
    except Exception as e:
        print(f"INSTALL_FAIL:{str(e)}")
        try:
            subprocess.run(['git', 'clone', 'https://github.com/LittleLearner-LL/LLM-Fifth-Grade-Only.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './LLM-Fifth-Grade-Only'], cwd='./LLM-Fifth-Grade-Only')
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")

def download_codebase():
    try:
        subprocess.run(['git', 'clone', 'https://github.com/LittleLearner-LL/LLM-Fifth-Grade-Only.git'], check=False)
    except Exception as e:
        print(f"TEST_FAIL:download_codebase:{str(e)}")

def run_model():
    try:
        import llm_fifth_grade_only
        start_time = time.time()
        tracemalloc.start()
        output = llm_fifth_grade_only.run_model("sample input")
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"BENCHMARK:run_model_latency_ms:{(end_time - start_time) * 1000}")
        print(f"BENCHMARK:run_model_memory_mb:{current / 10**6}")
        return output
    except Exception as e:
        print(f"TEST_FAIL:run_model:{str(e)}")
        return None

def compare_output():
    try:
        import llama
        baseline_output = llama.run_model("sample input")
        model_output = run_model()
        if model_output == baseline_output:
            print("TEST_PASS:compare_output")
        else:
            print("TEST_FAIL:compare_output:Output mismatch")
    except Exception as e:
        print(f"TEST_FAIL:compare_output:{str(e)}")

def compare_performance():
    try:
        import llama
        start_time = time.time()
        llm_fifth_grade_only.run_model("sample input")
        end_time = time.time()
        llama_time = time.time()
        llama.run_model("sample input")
        llama_end_time = time.time()
        ratio = (end_time - start_time) / (llama_end_time - llama_time)
        print(f"BENCHMARK:vs_llama_run_model_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:compare_performance:{str(e)}")

def measure_concept_understanding():
    try:
        import llm_fifth_grade_only
        concepts = ["concept1", "concept2", "concept3"]
        correct_count = 0
        for concept in concepts:
            output = llm_fifth_grade_only.run_model(concept)
            if output == "correct output":
                correct_count += 1
        print(f"BENCHMARK:concept_understanding_accuracy:{correct_count / len(concepts)}")
    except Exception as e:
        print(f"TEST_FAIL:measure_concept_understanding:{str(e)}")

def main():
    install_dependencies()
    download_codebase()
    start_import_time = time.time()
    import llm_fifth_grade_only
    end_import_time = time.time()
    print(f"BENCHMARK:import_time_ms:{(end_import_time - start_import_time) * 1000}")
    compare_output()
    compare_performance()
    measure_concept_understanding()
    print("RUN_OK")

if __name__ == "__main__":
    main()