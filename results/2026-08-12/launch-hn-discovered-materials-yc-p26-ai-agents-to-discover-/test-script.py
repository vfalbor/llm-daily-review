import subprocess
import sys
import time
import tracemalloc
import importlib.util
import numpy as np
from materials_modeling import train_model, predict

def install_packages():
    try:
        subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
        subprocess.run(['pip', 'install', 'materials-modeling'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        try:
            subprocess.run(['git', 'clone', 'https://github.com/discoveredmaterials/materials-modeling.git'], check=False)
            subprocess.run(['pip', 'install', '-e', './materials-modeling'], check=False, cwd='./materials-modeling')
            print("INSTALL_OK")
        except Exception as e:
            print(f"INSTALL_FAIL:{str(e)}")

def test_train_model():
    try:
        start_time = time.time()
        sample_data = np.random.rand(100, 10)
        model = train_model(sample_data)
        end_time = time.time()
        print(f"BENCHMARK:training_time_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:train_model")
    except Exception as e:
        print(f"TEST_FAIL:train_model:{str(e)}")

def test_predict():
    try:
        start_time = time.time()
        sample_data = np.random.rand(1, 10)
        prediction = predict(sample_data)
        end_time = time.time()
        print(f"BENCHMARK:prediction_time_ms:{(end_time - start_time) * 1000}")
        print(f"TEST_PASS:predict")
    except Exception as e:
        print(f"TEST_FAIL:predict:{str(e)}")

def compare_with_baseline():
    try:
        # Measure import time of materials-modeling and Materia
        start_time = time.time()
        importlib.import_module('materials_modeling')
        end_time = time.time()
        materials_import_time = end_time - start_time

        start_time = time.time()
        importlib.import_module('materia')
        end_time = time.time()
        materia_import_time = end_time - start_time

        ratio = materials_import_time / materia_import_time
        print(f"BENCHMARK:vs_materia_import_time_ratio:{ratio}")

        # Measure core operation latency of materials-modeling and Materia
        start_time = time.time()
        sample_data = np.random.rand(100, 10)
        train_model(sample_data)
        end_time = time.time()
        materials_latency = end_time - start_time

        start_time = time.time()
        # Call Materia's equivalent function
        # For demonstration purposes, assume it's called 'train_model' in Materia
        materia.train_model(sample_data)
        end_time = time.time()
        materia_latency = end_time - start_time

        ratio = materials_latency / materia_latency
        print(f"BENCHMARK:vs_materia_latency_ratio:{ratio}")
    except Exception as e:
        print(f"TEST_FAIL:compare_with_baseline:{str(e)}")

def main():
    install_packages()

    tracemalloc.start()
    start_time = time.time()
    try:
        import materials_modeling
    except Exception as e:
        print(f"TEST_FAIL:import_materials_modeling:{str(e)}")
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    print(f"BENCHMARK:import_memory_MB:{peak / 10**6}")
    print(f"BENCHMARK:import_time_ms:{(end_time - start_time) * 1000}")
    tracemalloc.stop()

    test_train_model()
    test_predict()
    compare_with_baseline()

    print("RUN_OK")

if __name__ == "__main__":
    main()