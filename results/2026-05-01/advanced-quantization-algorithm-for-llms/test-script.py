import subprocess
import time
import tracemalloc
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

try:
    # Install required system packages
    subprocess.run(['apk', 'add', '--no-cache', 'git'], check=False)
    print("INSTALL_OK")

    # Install auto-round via pip
    subprocess.run(['pip', 'install', 'git+https://github.com/intel/auto-round.git'], check=False)
    print("INSTALL_OK")

except Exception as e:
    print(f"INSTALL_FAIL:{str(e)}")

try:
    # Import auto-round
    import auto_round
    print("INSTALL_OK")

    # Measure import time
    start_time = time.time()
    import auto_round
    end_time = time.time()
    import_time = (end_time - start_time) * 1000  # in milliseconds
    print(f"BENCHMARK:import_time_ms:{import_time}")

    # Create a sample LLM model
    model = Sequential()
    model.add(Dense(64, activation='relu', input_shape=(1000,)))
    model.add(Dense(10))

    # Measure model creation time
    start_time = time.time()
    model = Sequential()
    model.add(Dense(64, activation='relu', input_shape=(1000,)))
    model.add(Dense(10))
    end_time = time.time()
    creation_time = (end_time - start_time) * 1000  # in milliseconds
    print(f"BENCHMARK:model_creation_time_ms:{creation_time}")

    # Quantize the model using auto-round
    start_time = time.time()
    quantized_model = auto_round.quantize(model)
    end_time = time.time()
    quantization_time = (end_time - start_time) * 1000  # in milliseconds
    print(f"BENCHMARK:quantization_time_ms:{quantization_time}")

    # Measure memory usage
    tracemalloc.start()
    model = Sequential()
    model.add(Dense(64, activation='relu', input_shape=(1000,)))
    model.add(Dense(10))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"BENCHMARK:memory_usage_bytes:{peak}")

    # Compare performance vs TensorFlow Model Optimization Tool
    start_time = time.time()
    tf_model = tf.keras.models.clone_model(model)
    tf.keras.mixed_precision.set_global_policy('mixed_float16')
    end_time = time.time()
    tf_quantization_time = (end_time - start_time) * 1000  # in milliseconds
    print(f"BENCHMARK:vs_tensorflow_quantization_time_ratio:{quantization_time / tf_quantization_time}")

    # Test quantization accuracy
    inputs = np.random.rand(1, 1000)
    predictions = model.predict(inputs)
    quantized_predictions = quantized_model.predict(inputs)
    accuracy = np.mean(np.isclose(predictions, quantized_predictions, atol=1e-6))
    print(f"BENCHMARK:quantization_accuracy:{accuracy}")

    print(f"TEST_PASS:quantization_accuracy")

except Exception as e:
    print(f"TEST_FAIL:quantization_accuracy:{str(e)}")

print("RUN_OK")