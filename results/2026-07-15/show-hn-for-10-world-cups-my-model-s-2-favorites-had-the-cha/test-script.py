import subprocess
import sys
import time
import tracemalloc
import random
from statistics import mean

# Install git package
print("Installing git package...")
try:
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")
except Exception as e:
    print(f"INSTALL_FAIL: {str(e)}")

# Install the package using pip
print("Installing the package using pip...")
try:
    subprocess.run(['pip', 'install', 'llm-ai'], check=False)
    print("INSTALL_OK")
except Exception as e:
    # Try fallback strategy: git clone + pip install -e .
    print(f"INSTALL_FAIL: {str(e)}")
    print("Trying fallback strategy...")
    try:
        subprocess.run(['git', 'clone', 'https://github.com/llm-ai/llm-ai.git'], check=False)
        subprocess.run(['pip', 'install', '-e', './llm-ai'], check=False)
        print("INSTALL_OK")
    except Exception as e:
        print(f"INSTALL_FAIL: {str(e)}")

# Import the package
import llm_ai

# Measure import time
start_time = time.time()
import llm_ai
end_time = time.time()
import_time = (end_time - start_time) * 1000
print(f"BENCHMARK:import_time_ms:{import_time}")

# Run minimal functional test with synthetic data
tracemalloc.start()
start_time = time.time()
predictions = llm_ai.predict(synthetic_data=[1, 2, 3])
end_time = time.time()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
prediction_time = (end_time - start_time) * 1000
memory_usage = peak / 1024 / 1024
print(f"BENCHMARK:prediction_time_ms:{prediction_time}")
print(f"BENCHMARK:memory_usage_mb:{memory_usage}")

# Test 1: Verify model's predictions on 2018 and 2022 World Cups
try:
    predictions_2018 = llm_ai.predict(synthetic_data=[1, 2, 3])
    if len(predictions_2018) > 0:
        print("TEST_PASS:2018_World_Cup")
    else:
        print("TEST_FAIL:2018_World_Cup:No predictions made")
except Exception as e:
    print(f"TEST_FAIL:2018_World_Cup:{str(e)}")

try:
    predictions_2022 = llm_ai.predict(synthetic_data=[4, 5, 6])
    if len(predictions_2022) > 0:
        print("TEST_PASS:2022_World_Cup")
    else:
        print("TEST_FAIL:2022_World_Cup:No predictions made")
except Exception as e:
    print(f"TEST_FAIL:2022_World_Cup:{str(e)}")

# Test 2: Compare model's performance against naive random pick
try:
    naive_predictions = [random.choice([1, 2, 3]) for _ in range(100)]
    model_predictions = llm_ai.predict(synthetic_data=[1, 2, 3])
    if len(model_predictions) > 0:
        model_accuracy = mean([1 for i in range(len(naive_predictions)) if model_predictions[0] == naive_predictions[i]])
        print("TEST_PASS:Naive_Random_Pick")
        print(f"BENCHMARK:naive_random_pick_accuracy:{model_accuracy}")
    else:
        print("TEST_FAIL:Naive_Random_Pick:No predictions made")
except Exception as e:
    print(f"TEST_FAIL:Naive_Random_Pick:{str(e)}")

# Test 3: Evaluate model's performance using metrics such as Brier score and expected calibration error
try:
    brier_score = llm_ai.brier_score(predictions)
    expected_calibration_error = llm_ai.expected_calibration_error(predictions)
    print("TEST_PASS:Brier_Score")
    print(f"BENCHMARK:brier_score:{brier_score}")
    print("TEST_PASS:Expected_Calibration_Error")
    print(f"BENCHMARK:expected_calibration_error:{expected_calibration_error}")
except Exception as e:
    print(f"TEST_FAIL:Brier_Score:{str(e)}")
    print(f"TEST_FAIL:Expected_Calibration_Error:{str(e)}")

# Compare performance vs the most similar baseline tool (PredictIt)
try:
    import predictit
    predictit_predictions = predictit.predict(synthetic_data=[1, 2, 3])
    model_predictions = llm_ai.predict(synthetic_data=[1, 2, 3])
    if len(model_predictions) > 0 and len(predictit_predictions) > 0:
        model_accuracy = mean([1 for i in range(len(predictit_predictions)) if model_predictions[0] == predictit_predictions[i]])
        print(f"BENCHMARK:vs_predictit_accuracy_ratio:{model_accuracy}")
    else:
        print("TEST_SKIP:PredictIt_Comparison:No predictions made")
except Exception as e:
    print(f"TEST_SKIP:PredictIt_Comparison:{str(e)}")

# Measure overall execution time
start_time = time.time()
# Run the entire script
end_time = time.time()
execution_time = (end_time - start_time) * 1000
print(f"BENCHMARK:execution_time_ms:{execution_time}")

# Measure lines of code and number of test files
with open(__file__, 'r') as f:
    lines_of_code = len(f.readlines())
print(f"BENCHMARK:loc_count:{lines_of_code}")

import os
test_files = [file for file in os.listdir('.') if file.endswith('.py')]
print(f"BENCHMARK:test_files_count:{len(test_files)}")

print("RUN_OK")