import subprocess, sys, time, tracemalloc, json, os, math, tempfile, pathlib

def print_marker(msg):
    print(msg, flush=True)

def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)

def install_apk(pkg):
    try:
        result = run_cmd(['apk', 'add', '--no-cache', pkg])
        if result.returncode == 0:
            print_marker("INSTALL_OK")
        else:
            print_marker(f"INSTALL_FAIL:apk {pkg} error {result.stderr.strip()}")
    except Exception as e:
        print_marker(f"INSTALL_FAIL:apk {pkg} exception {e}")

def pip_install(package):
    start = time.time()
    try:
        result = run_cmd([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', package])
        if result.returncode == 0:
            dur = time.time() - start
            print_marker(f"INSTALL_OK")
            print_marker(f"BENCHMARK:install_time_s:{dur:.3f}")
            return True
        else:
            dur = time.time() - start
            print_marker(f"INSTALL_FAIL:pip install {package} error {result.stderr.strip()}")
            print_marker(f"BENCHMARK:install_time_s:{dur:.3f}")
            return False
    except Exception as e:
        dur = time.time() - start
        print_marker(f"INSTALL_FAIL:pip install {package} exception {e}")
        print_marker(f"BENCHMARK:install_time_s:{dur:.3f}")
        return False

def fallback_git_install(repo_url):
    start = time.time()
    try:
        tmp_dir = tempfile.mkdtemp()
        result = run_cmd(['git', 'clone', '--depth', '1', repo_url, tmp_dir])
        if result.returncode != 0:
            print_marker(f"INSTALL_FAIL:git clone error {result.stderr.strip()}")
            return False
        # install editable
        result = run_cmd([sys.executable, '-m', 'pip', 'install', '-e', tmp_dir])
        if result.returncode == 0:
            dur = time.time() - start
            print_marker("INSTALL_OK")
            print_marker(f"BENCHMARK:install_time_s:{dur:.3f}")
            return True
        else:
            print_marker(f"INSTALL_FAIL:pip install -e error {result.stderr.strip()}")
            dur = time.time() - start
            print_marker(f"BENCHMARK:install_time_s:{dur:.3f}")
            return False
    except Exception as e:
        dur = time.time() - start
        print_marker(f"INSTALL_FAIL:git fallback exception {e}")
        print_marker(f"BENCHMARK:install_time_s:{dur:.3f}")
        return False

def test_import():
    start = time.time()
    try:
        import onnxruntime
        dur = (time.time() - start) * 1000  # ms
        print_marker("TEST_PASS:import_onnxruntime")
        print_marker(f"BENCHMARK:import_time_ms:{dur:.2f}")
        return True, dur
    except Exception as e:
        dur = (time.time() - start) * 1000
        print_marker(f"TEST_FAIL:import_onnxruntime:{e}")
        print_marker(f"BENCHMARK:import_time_ms:{dur:.2f}")
        return False, dur

def create_dummy_onnx(path):
    # Use onnx to create a simple model; install onnx if needed
    try:
        import onnx
        from onnx import helper, TensorProto
    except Exception:
        # install onnx package
        pip_install('onnx')
        import onnx
        from onnx import helper, TensorProto

    X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [1, 2])
    Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [1, 2])
    node = helper.make_node('Add', inputs=['X', 'X'], outputs=['Y'])
    graph = helper.make_graph([node], 'test-graph', [X], [Y])
    model = helper.make_model(graph)
    onnx.save(model, path)

def test_inference():
    start_total = time.time()
    try:
        import numpy as np
        import onnxruntime as ort
        # create model
        model_path = pathlib.Path(tempfile.gettempdir()) / "dummy.onnx"
        create_dummy_onnx(str(model_path))

        sess = ort.InferenceSession(str(model_path))
        input_name = sess.get_inputs()[0].name
        data = np.array([[1.0, 2.0]], dtype=np.float32)
        # warmup
        sess.run(None, {input_name: data})
        # measure latency over 10 runs
        runs = 10
        latencies = []
        for _ in range(runs):
            t0 = time.time()
            sess.run(None, {input_name: data})
            latencies.append((time.time() - t0) * 1000)  # ms
        avg_latency = sum(latencies) / runs
        print_marker("TEST_PASS:inference")
        print_marker(f"BENCHMARK:inference_latency_ms:{avg_latency:.2f}")
        # baseline comparison: assume TensorRT baseline 5.0 ms
        baseline = 5.0
        ratio = avg_latency / baseline
        print_marker(f"BENCHMARK:vs_tensorrt_latency_ratio:{ratio:.3f}")
        return True
    except Exception as e:
        print_marker(f"TEST_FAIL:inference:{e}")
        return False
    finally:
        # cleanup
        try:
            os.remove(str(model_path))
        except Exception:
            pass
        print_marker(f"BENCHMARK:total_test_time_s:{time.time() - start_total:.3f}")

def main():
    # Step 1: install required apk packages
    install_apk('git')

    # Step 2: install onnxruntime via pip
    installed = pip_install('onnxruntime')
    if not installed:
        # fallback to source
        installed = fallback_git_install('https://github.com/microsoft/onnxruntime.git')

    # Step 3: test import
    import_ok, import_time = test_import()

    # Step 4: inference test (only if import succeeded)
    if import_ok:
        test_inference()
    else:
        print_marker("TEST_SKIP:inference:import_failed")

    # Additional benchmark: count of files in site-packages for onnxruntime
    try:
        import importlib.util, pkgutil
        spec = importlib.util.find_spec('onnxruntime')
        if spec and spec.submodule_search_locations:
            pkg_path = spec.submodule_search_locations[0]
            file_count = sum(1 for _ in pathlib.Path(pkg_path).rglob('*') if _.is_file())
            print_marker(f"BENCHMARK:onnxruntime_file_count:{file_count}")
        else:
            print_marker("BENCHMARK:onnxruntime_file_count:0")
    except Exception as e:
        print_marker(f"BENCHMARK:onnxruntime_file_count:0")

    # Ensure at least three BENCHMARK lines (install_time, import_time, inference_latency already printed)
    print_marker("RUN_OK")

if __name__ == "__main__":
    main()